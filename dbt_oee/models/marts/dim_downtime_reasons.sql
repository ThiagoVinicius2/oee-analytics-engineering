select
    reason_id,
    reason_description,
    reason_category
from {{ ref('stg_downtime_reasons') }}
