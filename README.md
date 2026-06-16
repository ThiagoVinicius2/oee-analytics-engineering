# OEE Analytics — Pipeline de Dados Industriais

Pipeline de dados *end-to-end* que transforma dados de produção de uma fábrica em métricas de **OEE (Overall Equipment Effectiveness)**, usando um stack moderno de Analytics Engineering: **Python + DuckDB + dbt**.

> Projeto de portfólio com foco em modelagem dimensional, qualidade de dados e métricas de manufatura (Lean / Six Sigma).

## Sobre o projeto

O OEE é o principal indicador de eficiência da indústria, definido como:

**OEE = Disponibilidade × Performance × Qualidade**

Este projeto simula a exportação de um sistema MES (*Manufacturing Execution System*) e, a partir dos dados brutos, constrói um modelo analítico completo capaz de responder perguntas como:

- Qual o OEE de cada máquina e da fábrica como um todo?
- Quais são as principais causas de parada (análise de Pareto)?
- Como a eficiência varia entre máquinas, turnos e ao longo do tempo?

## Arquitetura

```
CSVs (MES)  ->  Python        ->  DuckDB           ->  dbt           ->  Dashboard
                (Extract/Load)     (Data Warehouse)     (Transform)
```

| Camada          | Ferramenta       | Responsabilidade                          |
|-----------------|------------------|-------------------------------------------|
| Ingestão        | Python (pandas)  | Gera e carrega os dados brutos            |
| Data Warehouse  | DuckDB           | Armazena as camadas raw, staging e marts  |
| Transformação   | dbt              | Modelagem dimensional, testes e docs      |
| Visualização    | (em construção)  | Dashboard de OEE                          |

## Modelo de dados (star schema)

**Fatos**
- `fct_production` — grão: uma corrida de produção. Contém os três componentes do OEE.
- `fct_downtime` — grão: um evento de parada.

**Dimensões**
- `dim_machines`, `dim_products`, `dim_operators`, `dim_shifts`, `dim_dates`, `dim_downtime_reasons`

A qualidade do modelo é garantida por **24 testes** automatizados do dbt (chaves únicas, integridade referencial entre fatos e dimensões e validação de domínios).

## Principais resultados

- **OEE geral da fábrica: 71,6%** — dentro da faixa típica da indústria ("world class" = 85%).
- **Gargalo identificado:** a *Prensa 2* opera com OEE de apenas **59,5%**, com desempenho abaixo da média nos três componentes — uma clara prioridade de melhoria contínua.
- **Maiores causas de parada (Pareto):** quebra mecânica, setup / troca de molde e falta de material concentram a maior parte do tempo perdido.

## Como executar

Pré-requisitos: Python 3.11+

```bash
# 1. Instalar as dependências
pip install -r requirements.txt

# 2. Gerar os dados brutos (CSVs que simulam o export do MES)
python ingestion/generate_data.py

# 3. Carregar os dados no data warehouse DuckDB
python ingestion/load_to_duckdb.py

# 4. Construir e testar o modelo dimensional
cd dbt_oee
dbt build

# 5. (Opcional) Gerar a documentação navegável do dbt
dbt docs generate && dbt docs serve
```

### Configuração do perfil do dbt

O dbt se conecta ao warehouse via `~/.dbt/profiles.yml` (fora do repositório, por convenção de segurança):

```yaml
oee:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: /caminho/absoluto/para/warehouse/oee.duckdb
      threads: 4
```

## Estrutura do projeto

```
.
├── ingestion/          # scripts de geração e carga (Python)
│   ├── generate_data.py
│   └── load_to_duckdb.py
├── data/raw/           # dados brutos em CSV
├── warehouse/          # data warehouse DuckDB (gerado, fora do Git)
├── dbt_oee/            # projeto dbt
│   ├── models/
│   │   ├── staging/    # limpeza 1:1 (views)
│   │   └── marts/      # star schema (tables)
│   └── macros/
└── docs/               # documentação e imagens
```

## Tecnologias

Python · pandas · DuckDB · dbt · SQL · Modelagem dimensional · Git

---

**Autor:** Thiago Vinicius