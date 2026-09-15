# Contract: Support Action Log (`data/local/actions.sqlite`)

Git-ignored (`*.sqlite`). Created on first write. Append-only: the application code contains
only `CREATE TABLE IF NOT EXISTS` and `INSERT` statements (tested by SQL-string scan).

```sql
CREATE TABLE IF NOT EXISTS support_actions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  logged_at_utc TEXT    NOT NULL,   -- ISO 8601
  record_id     TEXT    NOT NULL,   -- synthetic demo cohort key only
  model_version TEXT    NOT NULL,
  score         REAL    NOT NULL,
  band          TEXT    NOT NULL,
  acknowledged  INTEGER NOT NULL CHECK (acknowledged IN (0,1)),
  decision      TEXT    NOT NULL CHECK (decision IN ('record','dismiss','override')),
  action        TEXT    NOT NULL CHECK (action IN ('outreach_email','meeting_offer','resource_share','no_action')),
  reason        TEXT,               -- optional free text, adviser-entered
  session_id    TEXT                -- random per app process; not a user identity
);
```

Rules:

- No student identifiers, names, or contact details are ever stored; `record_id` is synthetic.
- No column for outcome labels exists; the app has no access to them.
- Rows are never read by any training or evaluation command. Enforced by a scan over `src/ssn`
  (`tests/app/test_actions_log.py::test_action_log_is_never_referenced_outside_the_app`): no module
  outside `src/ssn/app/` may reference the log at all. The store itself is
  `src/ssn/app/services/action_log.py`.
- Adviser-facing reads are allowed and stay inside the app: `latest_by_record()` supplies the
  Support Queue's handled/remaining status, and `rows_for()` supplies the per-record history on
  Student Review. Both read only what the adviser recorded; neither is a model input (FR-065).
- `actions export` writes `data/local/actions_export.csv` for local review only.
- Duplicate acknowledgements for the same `record_id` create additional rows; history is
  preserved.
