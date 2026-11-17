# Run log

The runner appends one summary after each real-run repeat. Entries are UTC and
record the run ID, model slug and exact configured model string, provider calls
(including retries), cache hits, final request errors, invalid rate, latency
summary, and stop reason. Mock and dry runs are not recorded here.

Entry format:

```text
- <date_utc> | `<run_id>` | `<model_slug>` (`<model_string>`): calls=<n>, cache_hits=<n>, errors=<n>, invalid_rate=<rate>, latency_s mean/min/max=<mean>/<min>/<max>, stop_reason=<reason>
```

No real runs recorded yet. Mock runs belong in temporary directories and are not
logged here.
