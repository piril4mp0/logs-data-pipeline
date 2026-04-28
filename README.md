# Sobre este projeto
Este projeto é uma pipeline completa de analise de logs de uma microtik, cobrindo desde o ETL com ingestão eficiente dos logs até armazenamento e analytics.

# Stack Tecnológica
Container -> Docker <br/>
ETL -> Apache Spark  <br/>
Armazenamento -> Clickhouse  <br/>
Gerenciar Notebooks Python -> Jupyter <br/>
Analytics -> Grafana <br/>

# Como rodar
1. docker compose up -d
2. abrir http://localhost:8123
3. abrir web SQL UI
4. inserir credenciais
    - user: admin
    - senha: admin

4. rodar a query abaixo no clickhouse:
```sql 
CREATE TABLE logs.router_logs
(
    timestamp DateTime,
    month UInt8,
    day UInt8,
    year UInt16,
    time String,
    service String,
    level LowCardinality(String),
    message String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, service);```
