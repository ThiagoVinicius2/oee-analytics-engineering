with source as (select * from {{ source('raw', 'production_runs') }})
select
    run_id,
    cast(production_date as date) as production_date,
    shift_id,
    machine_id,
    product_id,
    operator_id,
    planned_time_min,
    run_time_min,
    total_count,
    good_count,
    scrap_count
from source
