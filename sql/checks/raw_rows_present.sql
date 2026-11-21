-- severity: error
-- Each dataset must have at least some rows in the load window.
-- Every returned row is a failure.
select 'generation' as dataset
where not exists (
    select 1 from raw.fuel_type_hourly
    where period >= %(window_start)s and period < %(window_end)s
)
union all
select 'region'
where not exists (
    select 1 from raw.region_hourly
    where period >= %(window_start)s and period < %(window_end)s
);
