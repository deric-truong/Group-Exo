# Data cleaning decisions log

| Date | Source | Decision | Reason | Author |
|------|--------|----------|--------|--------|
| 2026-10-19 | CFTC | Index each report by its release date = next Friday after the measurement day | Avoid look-ahead bias; the old "+3 days" rule gave wrong days in holiday weeks | Deric |
| 2026-10-19 | CFTC | Flag reports measured during the Oct 2013 and Dec 2018–Jan 2019 US government shutdowns (`delayed_release`) and exclude them from event studies | They were published weeks late, so the next-Friday release date is wrong | Deric |

| 2026-11-01 | BIS | Keep the quarter-end date as index and add `release_date` = quarter end + 4 months; use `release_date` when aligning with market data | Avoid look-ahead bias: BIS publishes each quarter months after it ends | Deric |
| 2026-11-01 | BIS | Check units (`UNIT_MEASURE = JPY`, `UNIT_MULT = 6`) and duplicates on download; raise an error if they change | The conversion to trillions of yen relies on them | Deric |
| 2026-11-01 | BIS | Re-fetch rather than keep old files; past quarters are revised (e.g. 2025-Q3 went from 62.7 to 64.0 tn JPY) | BIS revises recent quarters in later releases | Deric |
