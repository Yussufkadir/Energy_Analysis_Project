-- Marts: analysis-ready tables that the dashboard and CSV exports read.
-- Missing hours are never filled in; every mart carries a count of reported
-- hours so incomplete days are visible rather than hidden.

create schema mart;

-- Daily generation by fuel, with each fuel's share of that day's total.
create table mart.daily_fuel_mix as
select
    period_local::date                          as date,
    respondent,
    respondent_name,
    respondent_level,
    fuel_code,
    fuel_name,
    fuel_group,
    is_renewable,
    sum(generation_mwh)                         as generation_mwh,
    count(generation_mwh)                       as hours_reported,
    round((100 * sum(generation_mwh)
        / nullif(sum(sum(generation_mwh)) over (partition by period_local::date, respondent), 0)
    )::numeric, 2)                              as share_pct
from staging.stg_generation
group by 1, 2, 3, 4, 5, 6, 7, 8;

-- Average generation by local hour of day and month, for "when does each
-- source run?" questions. Regions only: balancing authorities have no
-- local time zone mapped.
create table mart.hourly_profile as
select
    respondent,
    respondent_name,
    extract(month from period_local)::int       as month,
    extract(hour from period_local)::int        as hour_local,
    fuel_code,
    fuel_name,
    fuel_group,
    round(avg(generation_mwh)::numeric, 1)      as avg_generation_mwh,
    count(generation_mwh)                       as hours_reported
from staging.stg_generation
where respondent_level in ('country', 'region')
group by 1, 2, 3, 4, 5, 6, 7;

-- Daily demand, EIA's day-ahead forecast and how far off it was.
create table mart.daily_demand as
select
    period_local::date                                          as date,
    respondent,
    respondent_name,
    respondent_level,
    sum(demand_mwh)                                             as demand_mwh,
    sum(demand_forecast_mwh)                                    as demand_forecast_mwh,
    sum(net_generation_mwh)                                     as net_generation_mwh,
    sum(interchange_mwh)                                        as interchange_mwh,
    max(demand_mwh)                                             as peak_demand_mwh,
    (array_agg(extract(hour from period_local)::int
        order by demand_mwh desc nulls last))[1]                as peak_hour_local,
    round((100 * avg(abs(demand_mwh - demand_forecast_mwh) / nullif(demand_mwh, 0))
        filter (where demand_mwh > 0 and demand_forecast_mwh is not null))::numeric, 2)
                                                                as forecast_mape_pct,
    count(demand_mwh)                                           as hours_reported
from staging.stg_region
group by 1, 2, 3, 4;

-- Monthly roll-up per respondent: demand, generation by group and clean share.
create table mart.monthly_summary as
with gen as (
    select
        date_trunc('month', date)::date                              as month,
        respondent,
        respondent_name,
        respondent_level,
        sum(generation_mwh)                                          as generation_mwh,
        sum(generation_mwh) filter (where fuel_group = 'fossil')     as fossil_mwh,
        sum(generation_mwh) filter (where fuel_group = 'nuclear')    as nuclear_mwh,
        sum(generation_mwh) filter (where fuel_group = 'renewable')  as renewable_mwh,
        sum(generation_mwh) filter (where fuel_code = 'NG')          as natural_gas_mwh,
        sum(generation_mwh) filter (where fuel_code = 'COL')         as coal_mwh
    from mart.daily_fuel_mix
    group by 1, 2, 3, 4
),
dem as (
    select
        date_trunc('month', date)::date                              as month,
        respondent,
        sum(demand_mwh)                                              as demand_mwh,
        max(peak_demand_mwh)                                         as peak_demand_mwh
    from mart.daily_demand
    group by 1, 2
)
select
    gen.*,
    dem.demand_mwh,
    dem.peak_demand_mwh,
    round((100 * renewable_mwh / nullif(generation_mwh, 0))::numeric, 2)                  as renewable_share_pct,
    round((100 * (coalesce(renewable_mwh, 0) + coalesce(nuclear_mwh, 0))
        / nullif(generation_mwh, 0))::numeric, 2)                                         as clean_share_pct,
    round((100 * natural_gas_mwh / nullif(generation_mwh, 0))::numeric, 2)                as natural_gas_share_pct
from gen
left join dem using (month, respondent);

-- How complete is each series? Reported against the full loaded window.
create table mart.data_completeness as
with bounds as (
    select min(period) as first_hour, max(period) as last_hour,
           (extract(epoch from max(period) - min(period)) / 3600)::int + 1 as expected_hours
    from (select period from raw.fuel_type_hourly
          union all
          select period from raw.region_hourly) p
),
series as (
    select 'generation' as dataset, respondent, fueltype as series_code,
           count(*) as rows_present, count(value) as hours_with_value
    from raw.fuel_type_hourly group by 1, 2, 3
    union all
    select 'region', respondent, type,
           count(*), count(value)
    from raw.region_hourly group by 1, 2, 3
)
select
    s.dataset,
    s.respondent,
    s.series_code,
    b.first_hour,
    b.last_hour,
    b.expected_hours,
    s.hours_with_value,
    s.rows_present - s.hours_with_value                                          as null_hours,
    round((100.0 * s.hours_with_value / nullif(b.expected_hours, 0))::numeric, 2) as completeness_pct
from series s
cross join bounds b;
