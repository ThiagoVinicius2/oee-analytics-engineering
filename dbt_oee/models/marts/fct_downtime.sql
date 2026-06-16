select
    event_id,
    run_id,
    machine_id,
    reason_id,
    production_date,
    duration_min
from {{ ref('stg_downtime_events') }}
