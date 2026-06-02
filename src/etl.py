import sys
import time
import glob
import os
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, regexp_extract, to_timestamp, concat_ws

from settings import settings
from utils.helpers import ch_query, calc_md5
from utils.logger import logger

class LogETLPipeline:
    """
    Modular ETL Pipeline to process router logs and store them in ClickHouse.
    """
    LOG_PATTERN = r"^(\w{3}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2}) ([\w\-]+),(\w+): (.*)$"

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.abspath(os.path.join(self.script_dir, "..", "data"))
        self.lib_dir = os.path.abspath(os.path.join(self.script_dir, "..", "lib"))
        
        self.log_files = glob.glob(os.path.join(self.data_dir, "*.log"))
        self.pending = []
        self.skipped = []
        self.failed = []
        
        self.start_time = time.time()
        self.spark = None

    def setup_database(self):
        """Ensures the ClickHouse database and tables exist."""
        logger.info("Verificando/Criando tabelas no ClickHouse...")
        ch_query(f"CREATE DATABASE IF NOT EXISTS {settings.ch_database}")

        ch_query(f"""
            CREATE TABLE IF NOT EXISTS {settings.ch_database}.router_logs (
                timestamp DateTime,
                service   LowCardinality(String),
                level     LowCardinality(String),
                message   String
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(timestamp)
            ORDER BY (timestamp, service)
        """)

        ch_query(f"""
            CREATE TABLE IF NOT EXISTS {settings.ch_database}.file_hashes (
                file_hash    String,
                file_name    String,
                processed_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY file_hash
        """)

    def filter_processed_files(self):
        """Filters out files that have already been processed based on MD5 hashes."""
        seen_hashes = {}
        for path in sorted(self.log_files):
            file_hash = calc_md5(path)
            try:
                already = int(ch_query(
                    f"SELECT count() FROM {settings.ch_database}.file_hashes WHERE file_hash = '{file_hash}'"
                ))
                if already or file_hash in seen_hashes:
                    self.skipped.append(path)
                    logger.info(f"Pulando (já processado): {path}")
                else:
                    seen_hashes[file_hash] = path
                    self.pending.append((path, file_hash))
            except Exception as e:
                logger.error(f"Falha ao consultar ClickHouse para {path}: {e}")
                sys.exit(1)

    def init_spark(self):
        """Initializes and configures the SparkSession."""
        logger.info("Iniciando Spark Session...")
        jars = ",".join(glob.glob(os.path.join(self.lib_dir, "*.jar")))
        
        self.spark = (
            SparkSession.builder
            .config("spark.jars", jars)
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.default.parallelism", "8")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            .config("spark.sql.adaptive.skewJoin.enabled", "true")
            .config("spark.sql.autoBroadcastJoinThreshold", "10mb")
            .config("spark.shuffle.compress", "true")
            .config("spark.io.compression.codec", "lz4")
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            .config("spark.kryoserializer.buffer.max", "512m")
            .config("spark.clickhouse.ignoreUnsupportedTransform", "true")
            .getOrCreate()
        )

        configs = {
            "spark.sql.catalog.clickhouse":           "com.clickhouse.spark.ClickHouseCatalog",
            "spark.sql.catalog.clickhouse.host":      settings.ch_host,
            "spark.sql.catalog.clickhouse.protocol":  "http",
            "spark.sql.catalog.clickhouse.http_port": settings.ch_port,
            "spark.sql.catalog.clickhouse.user":      settings.ch_user,
            "spark.sql.catalog.clickhouse.password":  settings.ch_password,
            "spark.sql.catalog.clickhouse.database":  settings.ch_database,
            "spark.clickhouse.write.format":          "json",
            "spark.clickhouse.write.batchSize":       "100000",
            "spark.clickhouse.write.maxRetries":      "3",
        }
        
        for k, v in configs.items():
            self.spark.conf.set(k, v)

    def transform_logs(self, df: DataFrame) -> DataFrame:
        """Applies regex extraction and data transformations to the log DataFrame."""
        return (
            df.select(
                regexp_extract("value", self.LOG_PATTERN, 1).alias("date"),
                regexp_extract("value", self.LOG_PATTERN, 2).alias("time"),
                regexp_extract("value", self.LOG_PATTERN, 3).alias("service"),
                regexp_extract("value", self.LOG_PATTERN, 4).alias("level"),
                regexp_extract("value", self.LOG_PATTERN, 5).alias("message"),
            )
            .withColumn(
                "timestamp",
                to_timestamp(concat_ws(" ", col("date"), col("time")), "MMM/dd/yyyy HH:mm:ss")
            )
            .select("timestamp", "service", "level", "message")
        )

    def process_files(self):
        """Processes each pending file and writes the results to ClickHouse."""
        for path, file_hash in self.pending:
            logger.info(f"Processando: {path}")
            try:
                structured = self.transform_logs(self.spark.read.text(path))

                structured.writeTo("clickhouse.logs.router_logs").append()

                ch_query(
                    f"INSERT INTO {settings.ch_database}.file_hashes (file_hash, file_name, processed_at) "
                    f"VALUES ('{file_hash}', '{path}', now())"
                )
            except Exception as e:
                logger.error(f"{path}: {e}")
                self.failed.append(path)

    def report(self):
        """Logs the final processing report."""
        duration = time.time() - self.start_time
        logger.info(f"\n══ Relatório ══════════════════════")
        logger.info(f"  Encontrados:  {len(self.log_files)}")
        logger.info(f"  Pulados:      {len(self.skipped)}")
        logger.info(f"  Processados:  {len(self.pending) - len(self.failed)}")
        logger.info(f"  Erros:        {len(self.failed)}")
        for f in self.failed:
            logger.info(f"    ✗ {f}")
        logger.info(f"  Tempo total:  {duration:.2f}s")

    def run(self):
        """Orchestrates the ETL process."""
        logger.info(f"Iniciando | {len(self.log_files)} arquivo(s) encontrado(s).")

        if not self.log_files:
            logger.info("Nenhum arquivo de log encontrado. Encerrando.")
            return

        self.setup_database()
        self.filter_processed_files()

        if not self.pending:
            logger.info("Nenhum arquivo novo para processar.")
            self.report()
            return

        try:
            self.init_spark()
            self.process_files()
        finally:
            if self.spark:
                self.spark.stop()
            self.report()

if __name__ == "__main__":
    pipeline = LogETLPipeline()
    pipeline.run()
    sys.exit(1 if pipeline.failed else 0)
