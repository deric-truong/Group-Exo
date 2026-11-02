# Data cleaning decisions log

| Date | Source | Decision | Reason | Author |
|------|--------|----------|--------|--------|
| 2026-10-19 | CFTC | Index each report by its release date = next Friday after the measurement day | Avoid look-ahead bias; the old "+3 days" rule gave wrong days in holiday weeks | Deric |
| 2026-10-19 | CFTC | Flag reports measured during the Oct 2013 and Dec 2018–Jan 2019 US government shutdowns (`delayed_release`) and exclude them from event studies | They were published weeks late, so the next-Friday release date is wrong | Deric |

| 2026-11-01 | BIS | Keep the quarter-end date as index and add `release_date` = quarter end + 4 months; use `release_date` when aligning with market data | Avoid look-ahead bias: BIS publishes each quarter months after it ends | Deric |
| 2026-11-01 | BIS | Check units (`UNIT_MEASURE = JPY`, `UNIT_MULT = 6`) and duplicates on download; raise an error if they change | The conversion to trillions of yen relies on them | Deric |
| 2026-11-01 | BIS | Re-fetch rather than keep old files; past quarters are revised (e.g. 2025-Q3 went from 62.7 to 64.0 tn JPY) | BIS revises recent quarters in later releases | Deric |
| 2026-11-02 | Yahoo | Set one-day USD/JPY bad prints to NaN (`remove_spikes`): a jump >3% away from both neighbours, in the same direction, while the neighbours stay within 2% of each other. Removes 2008-04-08, 05-08, 10-08, 12-08 | Yahoo errors (e.g. 109.24 between 92.82 and 92.30) create fake extreme returns and bias the tail tests (H1) | Deric |
| 2026-11-02 | Yahoo | Apply this rule to USD/JPY only, not to equities, VIX, Bitcoin, oil or USD/MXN | In those series, big moves that reverse the next day are real (e.g. VIX, USD/MXN 2008-10-22 during the peso crisis) | Deric |
| 2026-11-02 | Yahoo | Keep weekend rows and do not forward-fill prices in the saved file | Weekend rows come from Bitcoin only; filling gaps would create fake zero returns. Alignment is done in the merge step | Deric |
