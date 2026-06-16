"""
Carregador (etapa Load do ELT).
Lê os CSVs de data/raw/ e os carrega no warehouse DuckDB,
no schema 'raw' — a camada de dados brutos do projeto.
"""

import glob
import os

import duckdb

RAW_DIR = "data/raw"
DB_PATH = "warehouse/oee.duckdb"

os.makedirs("warehouse", exist_ok=True)

con = duckdb.connect(DB_PATH)
con.execute("CREATE SCHEMA IF NOT EXISTS raw;")

csv_files = sorted(glob.glob(f"{RAW_DIR}/*.csv"))
if not csv_files:
    raise SystemExit("Nenhum CSV encontrado em data/raw/. Rode generate_data.py antes.")

print("Carregando CSVs no DuckDB...\n")
for path in csv_files:
    table = os.path.splitext(os.path.basename(path))[0]
    con.execute(
        f"CREATE OR REPLACE TABLE raw.{table} AS "
        f"SELECT * FROM read_csv_auto('{path}', header=true)"
    )
    n = con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
    print(f"  raw.{table:<18} {n:>6} linhas")

con.close()
print(f"\nWarehouse criado em {DB_PATH}")