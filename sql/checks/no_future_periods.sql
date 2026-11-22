-- severity: error
-- Timestamps after now mean a timezone or parsing bug.
select 'generation' as dataset, period from raw.fuel_type_hourly
where period > now() + interval '1 hour'
union all
select 'region', period from raw.region_hourly
where period > now() + interval '1 hour'
limit 20;
