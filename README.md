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
