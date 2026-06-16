with source as (select * from {{ source('raw', 'downtime_reasons') }})
select
    reason_id,
    reason_description,
    reason_category
from source
