with runs as (
    select * from {{ ref('stg_production_runs') }}
),

machines as (
    select machine_id, ideal_cycle_time_sec from {{ ref('stg_machines') }}
),

downtime as (
    select
        e.run_id,
        sum(e.duration_min) as downtime_min,
        sum(case when r.reason_category = 'Planejada'
                 then e.duration_min else 0 end) as planned_downtime_min,
        sum(case when r.reason_category = 'Não planejada'
                 then e.duration_min else 0 end) as unplanned_downtime_min
    from {{ ref('stg_downtime_events') }} e
    left join {{ ref('stg_downtime_reasons') }} r on e.reason_id = r.reason_id
    group by e.run_id
),

joined as (
    select
        runs.run_id,
        runs.production_date,
        runs.shift_id,
        runs.machine_id,
        runs.product_id,
        runs.operator_id,
        runs.planned_time_min,
        runs.run_time_min,
        coalesce(downtime.downtime_min, 0)            as downtime_min,
        coalesce(downtime.planned_downtime_min, 0)    as planned_downtime_min,
        coalesce(downtime.unplanned_downtime_min, 0)  as unplanned_downtime_min,
        runs.total_count,
        runs.good_count,
        runs.scrap_count,
        machines.ideal_cycle_time_sec
    from runs
    left join machines on runs.machine_id = machines.machine_id
    left join downtime  on runs.run_id   = downtime.run_id
),

oee_calc as (
    select
        *,
        -- Availability = tempo produzindo / tempo planejado
        round(run_time_min::double / nullif(planned_time_min, 0), 4) as availability,
        -- Performance = produzido / produção teórica no ritmo ideal
        least(round(
            total_count::double
            / nullif((run_time_min * 60.0) / nullif(ideal_cycle_time_sec, 0), 0)
        , 4), 1.0) as performance,
        -- Quality = peças boas / peças totais
        round(good_count::double / nullif(total_count, 0), 4) as quality
    from joined
)

select
    *,
    -- OEE = Availability x Performance x Quality
    round(availability * performance * quality, 4) as oee
from oee_calc
