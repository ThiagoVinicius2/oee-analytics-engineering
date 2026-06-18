"""
Exporta os marts (star schema) do DuckDB para CSV, prontos para
consumo em ferramentas de BI como Qlik Sense, Power BI, etc.
"""
import os
import duckdb

DB_PATH = "warehouse/oee.duckdb"
OUT = "export"
os.makedirs(OUT, exist_ok=True)

tables = [
    "fct_production", "fct_downtime",
    "dim_machines", "dim_products", "dim_operators",
    "dim_shifts", "dim_dates", "dim_downtime_reasons",
]

con = duckdb.connect(DB_PATH)
print("Exportando marts para CSV...\n")
for t in tables:
    con.execute(f"COPY marts.{t} TO '{OUT}/{t}.csv' (HEADER, DELIMITER ',')")
    n = con.execute(f"SELECT count(*) FROM marts.{t}").fetchone()[0]
    print(f"  {t:<22} {n:>6} linhas")
con.close()
print(f"\nCSVs exportados em {OUT}/")