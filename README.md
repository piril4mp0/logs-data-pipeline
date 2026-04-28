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