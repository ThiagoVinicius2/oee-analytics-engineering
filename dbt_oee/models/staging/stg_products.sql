with source as (select * from {{ source('raw', 'products') }})
select
    product_id,
    product_name,
    product_category
from source
