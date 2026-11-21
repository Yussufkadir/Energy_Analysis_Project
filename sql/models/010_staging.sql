-- Staging: clean, typed, enriched views over raw. No business logic yet.
-- The whole models folder runs in one transaction, so readers never see a
-- half-rebuilt warehouse.
--
-- EIA-930 timestamps are UTC and HOUR-ENDING (form EIA-930 instructions:
-- "hourly integrated values ... by hour ending time"), so raw period
-- 15:00 covers 14:00-15:00. Staging converts to hour-beginning:
-- period_local and every date / hour-of-day derived from it refer to the
-- start of the hour, so the hour ending at midnight counts toward the day
-- it belongs to.

drop schema if exists mart cascade;
drop schema if exists staging cascade;
create schema staging;

create view staging.stg_generation as
select
    g.period - interval '1 hour'                          as period_start_utc,
    g.period                                              as period_end_utc,
    ((g.period - interval '1 hour')
        at time zone coalesce(r.timezone, 'UTC'))         as period_local,
    g.respondent,
    coalesce(r.region_name, g.respondent_name)            as respondent_name,
    coalesce(r.level, 'balancing_authority')              as respondent_level,
    g.fueltype                                            as fuel_code,
    coalesce(f.fuel_name, g.type_name, g.fueltype)        as fuel_name,
    coalesce(f.fuel_group, 'other')                       as fuel_group,
    coalesce(f.is_renewable, false)                       as is_renewable,
    g.value                                               as generation_mwh
from raw.fuel_type_hourly g
left join ref.fuel_type f on f.fuel_code = g.fueltype
left join ref.region r    on r.respondent = g.respondent;

-- Long (one row per metric) -> wide (one row per respondent-hour).
create view staging.stg_region as
select
    rh.period - interval '1 hour'                               as period_start_utc,
    rh.period                                                   as period_end_utc,
    ((rh.period - interval '1 hour')
        at time zone coalesce(r.timezone, 'UTC'))               as period_local,
    rh.respondent,
    coalesce(r.region_name, max(rh.respondent_name))            as respondent_name,
    coalesce(r.level, 'balancing_authority')                    as respondent_level,
    max(rh.value) filter (where rh.type = 'D')                  as demand_mwh,
    max(rh.value) filter (where rh.type = 'DF')                 as demand_forecast_mwh,
    max(rh.value) filter (where rh.type = 'NG')                 as net_generation_mwh,
    max(rh.value) filter (where rh.type = 'TI')                 as interchange_mwh
from raw.region_hourly rh
left join ref.region r on r.respondent = rh.respondent
group by rh.period, rh.respondent, r.timezone, r.region_name, r.level;
