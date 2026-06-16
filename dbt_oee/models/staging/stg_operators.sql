with source as (select * from {{ source('raw', 'operators') }})
select
    operator_id,
    operator_name,
    shift_id
from source
