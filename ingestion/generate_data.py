"""
Gerador de dados sintéticos — simula a exportação de um sistema MES
(Manufacturing Execution System) de uma fábrica.

Produz 7 tabelas-fonte em CSV (5 dimensões + 2 fatos):
  - machines.csv          (dimensão: máquinas)
  - products.csv          (dimensão: produtos)
  - operators.csv         (dimensão: operadores)
  - shifts.csv            (dimensão: turnos)
  - downtime_reasons.csv  (dimensão: motivos de parada)
  - production_runs.csv    (fato: um registro por corrida de produção)
  - downtime_events.csv    (fato: um registro por evento de parada)

Os dados são realistas o bastante para calcular OEE
(Availability x Performance x Quality), Pareto de paradas e MTBF/MTTR.
"""

import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

OUT = "data/raw"
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------
# 1) DIMENSÃO: turnos
# ----------------------------------------------------------------------
shifts = pd.DataFrame(
    [
        {"shift_id": "T1", "shift_name": "Manhã", "start_hour": 6, "end_hour": 14},
        {"shift_id": "T2", "shift_name": "Tarde", "start_hour": 14, "end_hour": 22},
        {"shift_id": "T3", "shift_name": "Noite", "start_hour": 22, "end_hour": 6},
    ]
)

# ----------------------------------------------------------------------
# 2) DIMENSÃO: máquinas (cada uma com um perfil de desempenho próprio)
# ----------------------------------------------------------------------
machines = pd.DataFrame(
    [
        # id   nome             linha       ciclo(s) avail perf  qual
        ("M01", "Extrusora A",  "Linha 1", 12, 0.90, 0.95, 0.98),
        ("M02", "Extrusora B",  "Linha 1", 12, 0.82, 0.90, 0.96),
        ("M03", "Prensa 1",     "Linha 1", 20, 0.88, 0.93, 0.97),
        ("M04", "Prensa 2",     "Linha 2", 20, 0.78, 0.88, 0.94),  # máquina-problema
        ("M05", "Montadora",    "Linha 2",  8, 0.92, 0.96, 0.99),
        ("M06", "Embaladora",   "Linha 2",  5, 0.85, 0.91, 0.97),
        ("M07", "Injetora A",   "Linha 3", 15, 0.87, 0.92, 0.97),
        ("M08", "Injetora B",   "Linha 3", 15, 0.80, 0.89, 0.95),
        ("M09", "Cortadeira",   "Linha 3", 10, 0.89, 0.94, 0.98),
        ("M10", "Soldadora",    "Linha 2", 18, 0.83, 0.90, 0.96),
        ("M11", "Forno",        "Linha 1", 25, 0.91, 0.93, 0.98),
        ("M12", "Pintura",      "Linha 3", 30, 0.76, 0.87, 0.93),  # 2ª máquina-problema
    ],
    columns=[
        "machine_id", "machine_name", "production_line",
        "ideal_cycle_time_sec", "avail_base", "perf_base", "qual_base",
    ],
)

# ----------------------------------------------------------------------
# 3) DIMENSÃO: produtos
# ----------------------------------------------------------------------
products = pd.DataFrame(
    [
        ("P01", "Pneu Aro 15",      "Pneus"),
        ("P02", "Pneu Aro 16",      "Pneus"),
        ("P03", "Câmara de ar",     "Acessórios"),
        ("P04", "Protetor de aro",  "Acessórios"),
        ("P05", "Borracha vulcan.", "Matéria-prima"),
    ],
    columns=["product_id", "product_name", "product_category"],
)

# ----------------------------------------------------------------------
# 4) DIMENSÃO: operadores (cada um pertence a um turno)
# ----------------------------------------------------------------------
first_names = [
    "Ana", "Bruno", "Carla", "Diego", "Elaine", "Felipe",
    "Gabriela", "Henrique", "Iara", "João", "Karen", "Lucas",
    "Mariana", "Nelson", "Olívia", "Paulo", "Rafaela", "Sérgio",
]
op_rows = []
for i, nome in enumerate(first_names):
    op_rows.append(
        {
            "operator_id": f"OP{i+1:02d}",
            "operator_name": nome,
            "shift_id": shifts["shift_id"].iloc[i % 3],
        }
    )
operators = pd.DataFrame(op_rows)

# ----------------------------------------------------------------------
# 5) DIMENSÃO: motivos de parada (com categoria planejada/não planejada
#    e peso para gerar um Pareto realista)
# ----------------------------------------------------------------------
downtime_reasons = pd.DataFrame(
    [
        # id    descrição                 categoria          peso  dur_média(min)
        ("R01", "Setup / troca de molde", "Planejada",       15,   25),
        ("R02", "Manutenção preventiva",  "Planejada",        5,   45),
        ("R03", "Parada programada",      "Planejada",        8,   20),
        ("R04", "Quebra mecânica",        "Não planejada",   12,   40),
        ("R05", "Falta de material",      "Não planejada",   18,   18),
        ("R06", "Ajuste de processo",     "Não planejada",   14,   12),
        ("R07", "Falha elétrica",         "Não planejada",    7,   35),
        ("R08", "Falta de operador",      "Não planejada",    6,   22),
        ("R09", "Pequenas paradas",       "Não planejada",   20,    5),
        ("R10", "Limpeza",                "Planejada",        9,   10),
        ("R11", "Troca de turno",         "Planejada",        7,    8),
        ("R12", "Inspeção de qualidade",  "Não planejada",    6,   15),
        ("R13", "Falha de sensor",        "Não planejada",    5,   20),
        ("R14", "Reabastecimento",        "Não planejada",   10,    8),
        ("R15", "Calibração",             "Planejada",        4,   18),
    ],
    columns=[
        "reason_id", "reason_description", "reason_category",
        "_weight", "_avg_duration_min",
    ],
)

reason_ids = downtime_reasons["reason_id"].tolist()
reason_weights = np.array(downtime_reasons["_weight"], dtype=float)
reason_weights = reason_weights / reason_weights.sum()
reason_avg = dict(zip(downtime_reasons["reason_id"], downtime_reasons["_avg_duration_min"]))

# ----------------------------------------------------------------------
# 6) FATOS: corridas de produção + eventos de parada
# ----------------------------------------------------------------------
PLANNED_TIME_MIN = 480          # 8 horas por turno
START_DATE = date(2024, 7, 1)
NUM_DAYS = 548                   # ~18 meses

prod_rows = []
event_rows = []
run_counter = 0
event_counter = 0

for d in range(NUM_DAYS):
    current = START_DATE + timedelta(days=d)
    # fins de semana têm produção reduzida
    is_weekend = current.weekday() >= 5

    for _, shift in shifts.iterrows():
        for _, m in machines.iterrows():
            # nem toda máquina roda em todo turno
            schedule_prob = 0.55 if is_weekend else 0.9
            if random.random() > schedule_prob:
                continue

            run_counter += 1
            run_id = f"RUN{run_counter:05d}"

            # --- paradas desta corrida ---
            # a disponibilidade-alvo depende do perfil da máquina:
            # máquina-problema (avail_base baixo) acumula mais paradas
            target_avail = float(
                np.clip(np.random.normal(m["avail_base"], 0.05), 0.55, 0.99)
            )
            target_downtime = PLANNED_TIME_MIN * (1 - target_avail)

            total_downtime = 0
            run_events = []
            while total_downtime < target_downtime:
                reason = np.random.choice(reason_ids, p=reason_weights)
                base = reason_avg[reason]
                dur = max(1, int(np.random.exponential(base)))
                run_events.append((reason, dur))
                total_downtime += dur

            # limita a parada a no máximo 45% do tempo planejado
            cap = int(PLANNED_TIME_MIN * 0.45)
            if total_downtime > cap:
                fator = cap / total_downtime
                run_events = [(r, max(1, int(dur * fator))) for r, dur in run_events]
                total_downtime = sum(dur for _, dur in run_events)

            run_time = PLANNED_TIME_MIN - total_downtime

            # --- contagem de peças (Performance e Quality) ---
            perf = float(np.clip(np.random.normal(m["perf_base"], 0.04), 0.6, 1.0))
            qual = float(np.clip(np.random.normal(m["qual_base"], 0.02), 0.7, 1.0))

            theoretical = (run_time * 60) / m["ideal_cycle_time_sec"]
            total_count = int(theoretical * perf)
            good_count = int(total_count * qual)
            scrap_count = total_count - good_count

            # operador do turno + produto aleatório
            ops_shift = operators[operators["shift_id"] == shift["shift_id"]]
            operator_id = ops_shift["operator_id"].sample(1).iloc[0]
            product_id = products["product_id"].sample(1).iloc[0]

            prod_rows.append(
                {
                    "run_id": run_id,
                    "production_date": current.isoformat(),
                    "shift_id": shift["shift_id"],
                    "machine_id": m["machine_id"],
                    "product_id": product_id,
                    "operator_id": operator_id,
                    "planned_time_min": PLANNED_TIME_MIN,
                    "run_time_min": run_time,
                    "total_count": total_count,
                    "good_count": good_count,
                    "scrap_count": scrap_count,
                }
            )

            for reason, dur in run_events:
                event_counter += 1
                event_rows.append(
                    {
                        "event_id": f"EVT{event_counter:06d}",
                        "run_id": run_id,
                        "machine_id": m["machine_id"],
                        "production_date": current.isoformat(),
                        "reason_id": reason,
                        "duration_min": dur,
                    }
                )

production_runs = pd.DataFrame(prod_rows)
downtime_events = pd.DataFrame(event_rows)

# ----------------------------------------------------------------------
# 7) salva os CSVs (sem as colunas auxiliares "_")
# ----------------------------------------------------------------------
machines.drop(columns=["avail_base", "perf_base", "qual_base"]).to_csv(
    f"{OUT}/machines.csv", index=False
)
products.to_csv(f"{OUT}/products.csv", index=False)
operators.to_csv(f"{OUT}/operators.csv", index=False)
shifts.to_csv(f"{OUT}/shifts.csv", index=False)
downtime_reasons.drop(columns=["_weight", "_avg_duration_min"]).to_csv(
    f"{OUT}/downtime_reasons.csv", index=False
)
production_runs.to_csv(f"{OUT}/production_runs.csv", index=False)
downtime_events.to_csv(f"{OUT}/downtime_events.csv", index=False)

print("Dados gerados com sucesso em", OUT)
print(f"  production_runs : {len(production_runs):>6} linhas")
print(f"  downtime_events : {len(downtime_events):>6} linhas")