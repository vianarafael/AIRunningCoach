PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS metrics (
  date TEXT PRIMARY KEY,
  resting_hr INTEGER,
  hrv_rmssd REAL, -- Heart Rate Variability - Root Mean Square of Successive Differences
  vo2max REAL,
  weight_kg REAL,
  sleep_hours REAL
);

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  ts_start TEXT, ts_end TEXT, -- start and end time of the session 
  sport TEXT,
  distance_m REAL, duration_s REAL,
  kcal REAL, avg_hr REAL, max_hr REAL,  
  device TEXT, training_load REAL
);

CREATE TABLE IF NOT EXISTS training_aggregates ( -- weekly rollups (volume + load) 
  year_week TEXT PRIMARY KEY,
  km REAL, load_7d REAL, load_28d REAL,
  acwr REAL, monotony REAL, strain REAL
);

CREATE TABLE IF NOT EXISTS etl_log ( -- enables incremental fetches + debugging
  run_ts TEXT PRIMARY KEY,
  ok INTEGER,
  notes TEXT 
);

CREATE INDEX IF NOT EXISTS idx_session_start ON sessions(ts_start);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(date);
