with source as (select * from {{ source('raw', 'downtime_events') }})
select
    event_id,
    run_id,
    machine_id,
    cast(production_date as date) as production_date,
    reason_id,
    duration_min
from source
