-- Reference data the API doesn't provide: fuel groupings and region time zones.

create schema if not exists ref;

create table if not exists ref.fuel_type (
    fuel_code     text primary key,
    fuel_name     text    not null,
    fuel_group    text    not null,   -- fossil | nuclear | renewable | storage | other
    is_renewable  boolean not null
);

insert into ref.fuel_type (fuel_code, fuel_name, fuel_group, is_renewable) values
    ('COL', 'Coal',                 'fossil',    false),
    ('NG',  'Natural gas',          'fossil',    false),
    ('OIL', 'Petroleum',            'fossil',    false),
    ('NUC', 'Nuclear',              'nuclear',   false),
    ('SUN', 'Solar',                'renewable', true),
    ('SNB', 'Solar with battery',   'renewable', true),
    ('WND', 'Wind',                 'renewable', true),
    ('WAT', 'Hydro',                'renewable', true),
    ('GEO', 'Geothermal',           'renewable', true),
    ('BAT', 'Battery storage',      'storage',   false),
    ('PS',  'Pumped storage',       'storage',   false),
    ('OES', 'Other energy storage', 'storage',   false),
    ('UES', 'Unknown energy storage','storage',  false),
    ('OTH', 'Other',                'other',     false),
    ('UNK', 'Unknown',              'other',     false)
on conflict (fuel_code) do update
    set fuel_name = excluded.fuel_name,
        fuel_group = excluded.fuel_group,
        is_renewable = excluded.is_renewable;

-- EIA timestamps are UTC. To answer "what time of day does demand peak?"
-- each region gets a representative local time zone. Balancing authorities
-- not listed here are reported in UTC.
create table if not exists ref.region (
    respondent   text primary key,
    region_name  text not null,
    level        text not null,   -- country | region
    timezone     text not null
);

insert into ref.region (respondent, region_name, level, timezone) values
    ('US48', 'United States Lower 48', 'country', 'America/Chicago'),  -- spans 4 zones; Central as midpoint
    ('CAL',  'California',             'region',  'America/Los_Angeles'),
    ('CAR',  'Carolinas',              'region',  'America/New_York'),
    ('CENT', 'Central',                'region',  'America/Chicago'),
    ('FLA',  'Florida',                'region',  'America/New_York'),
    ('MIDA', 'Mid-Atlantic',           'region',  'America/New_York'),
    ('MIDW', 'Midwest',                'region',  'America/Chicago'),
    ('NE',   'New England',            'region',  'America/New_York'),
    ('NY',   'New York',               'region',  'America/New_York'),
    ('NW',   'Northwest',              'region',  'America/Los_Angeles'),
    ('SE',   'Southeast',              'region',  'America/Chicago'),
    ('SW',   'Southwest',              'region',  'America/Phoenix'),
    ('TEN',  'Tennessee',              'region',  'America/Chicago'),
    ('TEX',  'Texas',                  'region',  'America/Chicago')
on conflict (respondent) do update
    set region_name = excluded.region_name,
        level = excluded.level,
        timezone = excluded.timezone;
