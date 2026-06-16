select
    o.operator_id,
    o.operator_name,
    o.shift_id,
    s.shift_name
from {{ ref('stg_operators') }} o
left join {{ ref('stg_shifts') }} s on o.shift_id = s.shift_id
