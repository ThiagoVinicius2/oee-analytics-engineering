with bounds as (
    select min(production_date) as lo, max(production_date) as hi
    from {{ ref('stg_production_runs') }}
),
spine as (
    select unnest(generate_series(lo, hi, interval 1 day))::date as date_day
    from bounds
)
select
    date_day,
    extract(year  from date_day) as year,
    extract(month from date_day) as month,
    extract(day   from date_day) as day,
    strftime(date_day, '%Y-%m')  as year_month,
    case extract(month from date_day)
        when 1 then 'Janeiro'  when 2 then 'Fevereiro' when 3 then 'Março'
        when 4 then 'Abril'    when 5 then 'Maio'      when 6 then 'Junho'
        when 7 then 'Julho'    when 8 then 'Agosto'    when 9 then 'Setembro'
        when 10 then 'Outubro' when 11 then 'Novembro' when 12 then 'Dezembro'
    end as month_name,
    extract(dow from date_day) as day_of_week,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from spine
