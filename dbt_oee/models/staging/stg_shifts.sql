with source as (select * from {{ source('raw', 'shifts') }})
select
    shift_id,
    shift_name,
    start_hour,
    end_hour
from source
