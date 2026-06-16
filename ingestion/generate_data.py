"""
Gerador de dados sintéticos — simula a exportação de um sistema MES
(Manufacturing Execution System) de uma fábrica.
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

# 1) DIMENSÃO: turnos
shifts = pd.DataFrame(
    [
        {"shift_id": "T1", "shift_name": "Manhã", "start_hour": 6, "end_hour": 14},
        {"shift_id": "T2", "shift_name": "Tarde", "start_hour": 14, "end_hour": 22},
        {"shift_id": "T3", "shift_name": "Noite", "start_hour": 22, "end_hour": 6},
    ]
)

# 2) DIMENSÃO: máquinas (cada uma com um perfil de desempenho próprio)
machines = pd.DataFrame(
    [
        ("M01", "Extrusora A", "Linha 1", 12, 0.90, 0.95, 0.98),
        ("M02", "Extrusora B", "Linha 1", 12, 0.82, 0.90, 0.96),
        ("M03", "Prensa 1", "Linha 1", 20, 0.88, 0.93, 0.97),
        ("M04", "Prensa 2", "Linha 2", 20, 0.78, 0.88, 0.94),
        ("M05", "Montadora", "Linha 2", 8, 0.92, 0.96, 0.99),
        ("M06", "Embaladora", "Linha 2", 5, 0.85, 0.91, 0.97),
    ],
    columns=[
        "machine_id", "machine_name", "production_line",
        "ideal_cycle_time_sec", "avail_base", "perf_base", "qual_base",
    ],
)

# 3) DIMENSÃO: produtos
products = pd.DataFrame(
    [
        ("P01", "Pneu Aro 15", "Pneus"),
        ("P02", "Pneu Aro 16", "Pneus"),
        ("P03", "Câmara de ar", "Acessórios"),
        ("P04", "Protetor de aro", "Acessórios"),
        ("P05", "Borracha vulcan.", "Matéria-prima"),
    ],
    columns=["product_id", "product_name", "product_category"],
)

# 4) DIMENSÃO: operadores (cada um pertence a um turno)
first_names = [
    "Ana", "Bruno", "Carla", "Diego", "Elaine", "Felipe",
    "Gabriela", "Henrique", "Iara", "João", "Karen", "Lucas",
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

# 5) DIMENSÃO: motivos de parada (categoria + peso para gerar um Pareto)
downtime_reasons = pd.DataFrame(
    [
        ("R01", "Setup / troca de molde", "Planejada", 15, 25),
        ("R02", "Manutenção preventiva", "Planejada", 5, 45),
        ("R03", "Parada programada", "Planejada", 8, 20),
        ("R04", "Quebra mecânica", "Não planejada", 12, 40),
        ("R05", "Falta de material", "Não planejada", 18, 18),
        ("R06", "Ajuste de processo", "Não planejada", 14, 12),
        ("R07", "Falha elétrica", "Não planejada", 7, 35),
        ("R08", "Falta de operador", "Não planejada", 6, 22),
        ("R09", "Pequenas paradas", "Não planejada", 20, 5),
        ("R10", "Limpeza", "Planejada", 9, 10),
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

# 6) FATOS: corridas de produção + eventos de parada
PLANNED_TIME_MIN = 480
START_DATE = date(2025, 1, 1)
NUM_DAYS = 180

prod_rows = []
event_rows = []
run_counter = 0
event_counter = 0

for d in range(NUM_DAYS):
    current = START_DATE + timedelta(days=d)
    is_weekend = current.weekday() >= 5

    for _, shift in shifts.iterrows():
        for _, m in machines.iterrows():
            schedule_prob = 0.55 if is_weekend else 0.9
            if random.random() > schedule_prob:
                continue

            run_counter += 1
            run_id = f"RUN{run_counter:05d}"

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

            cap = int(PLANNED_TIME_MIN * 0.45)
            if total_downtime > cap:
                fator = cap / total_downtime
                run_events = [(r, max(1, int(dur * fator))) for r, dur in run_events]
                total_downtime = sum(dur for _, dur in run_events)

            run_time = PLANNED_TIME_MIN - total_downtime

            perf = float(np.clip(np.random.normal(m["perf_base"], 0.04), 0.6, 1.0))
            qual = float(np.clip(np.random.normal(m["qual_base"], 0.02), 0.7, 1.0))

            theoretical = (run_time * 60) / m["ideal_cycle_time_sec"]
            total_count = int(theoretical * perf)
            good_count = int(total_count * qual)
            scrap_count = total_count - good_count

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

# 7) salva os CSVs (sem as colunas auxiliares "_")
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