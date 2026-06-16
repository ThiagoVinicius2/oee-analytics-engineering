with source as (select * from {{ source('raw', 'machines') }})
select
    machine_id,
    machine_name,
    production_line,
    ideal_cycle_time_sec
from source
