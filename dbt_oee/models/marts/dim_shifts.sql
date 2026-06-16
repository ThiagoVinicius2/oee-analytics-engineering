select
    shift_id,
    shift_name,
    start_hour,
    end_hour
from {{ ref('stg_shifts') }}
