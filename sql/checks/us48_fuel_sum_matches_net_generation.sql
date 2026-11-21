-- severity: warn
-- Generation summed across fuels should roughly equal reported net
-- generation. A gap of more than 5 percent is logged but doesn't fail the run,
-- because EIA itself publishes small inconsistencies.
with fuel as (
    select period, sum(value) as fuel_sum_mwh
    from raw.fuel_type_hourly
    where respondent = 'US48'
      and period >= %(window_start)s and period < %(window_end)s
    group by period
),
ng as (
    select period, value as net_generation_mwh
    from raw.region_hourly
    where respondent = 'US48' and type = 'NG'
      and period >= %(window_start)s and period < %(window_end)s
)
select period, fuel_sum_mwh, net_generation_mwh
from fuel join ng using (period)
where abs(fuel_sum_mwh - net_generation_mwh) > 0.05 * nullif(net_generation_mwh, 0)
limit 20;
