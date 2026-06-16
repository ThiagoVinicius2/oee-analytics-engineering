select
    machine_id,
    machine_name,
    production_line,
    ideal_cycle_time_sec
from {{ ref('stg_machines') }}
