# Data cleaning decisions log

| Date | Source | Decision | Reason | Author |
|------|--------|----------|--------|--------|
| 2026-10-19 | CFTC | Index each report by its release date = next Friday after the measurement day | Avoid look-ahead bias; the old "+3 days" rule gave wrong days in holiday weeks | Deric |
| 2026-10-19 | CFTC | Flag reports measured during the Oct 2013 and Dec 2018–Jan 2019 US government shutdowns (`delayed_release`) and exclude them from event studies | They were published weeks late, so the next-Friday release date is wrong | Deric |

