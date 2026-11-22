-- severity: error
-- Lower-48 hourly demand has stayed roughly between 300 and 760 GW.
-- Values far outside that range mean bad source data or a unit mix-up.
select period, value as demand_mwh
from raw.region_hourly
where respondent = 'US48'
  and type = 'D'
  and period >= %(window_start)s and period < %(window_end)s
  and (value < 200000 or value > 1000000)
limit 20;
