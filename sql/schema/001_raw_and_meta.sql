-- Raw layer: one row per API record, keyed on the source's natural key.
-- Loads are upserts, so re-running any window is idempotent and picks up
-- values EIA revised after first publication.

create schema if not exists raw;
create schema if not exists meta;

create table if not exists raw.fuel_type_hourly (
    period           timestamptz not null,   -- UTC, hour-ENDING (as EIA publishes it)
    respondent       text        not null,   -- balancing authority / region code
    respondent_name  text,
    fueltype         text        not null,   -- COL, NG, NUC, SUN, WND, WAT, OIL, OTH, ...
    type_name        text,
    value            double precision,       -- MWh; NULL when EIA has no value
    value_units      text,
    loaded_at        timestamptz not null default now(),
    primary key (period, respondent, fueltype)
);

create table if not exists raw.region_hourly (
    period           timestamptz not null,
    respondent       text        not null,
    respondent_name  text,
    type             text        not null,   -- D demand, DF day-ahead forecast, NG net generation, TI interchange
    type_name        text,
    value            double precision,
    value_units      text,
    loaded_at        timestamptz not null default now(),
    primary key (period, respondent, type)
);

create index if not exists fuel_type_hourly_respondent_period_idx
    on raw.fuel_type_hourly (respondent, period);
create index if not exists region_hourly_respondent_period_idx
    on raw.region_hourly (respondent, period);

-- One row per load, so you can see what every pipeline run actually did.
create table if not exists meta.load_log (
    id            bigserial primary key,
    dataset       text        not null,
    window_start  timestamptz not null,
    window_end    timestamptz not null,
    received      integer     not null,
    accepted      integer     not null,
    duplicates    integer     not null,
    null_values   integer     not null,
    rejected      integer     not null,
    loaded_at     timestamptz not null default now()
);
