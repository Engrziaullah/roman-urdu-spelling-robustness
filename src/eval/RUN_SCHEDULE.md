# NU and full-condition run schedule (planned)

Generated from `python -m src.eval.plan_runs --items data\processed\items_nu.jsonl --conditions NU,RU-P,RU-R,RU-X,RT` on 2026-11-24 (local). This is an estimate only (no provider calls).

| model_slug | requests_per_minute | requests_per_day | full_pass_requests | noise_extra_requests | estimated_days |
|---|---:|---:|---:|---:|---:|
| model-1 | 20 | 1000 | 2500 | 300 | 3 |
| model-2 | unknown | unknown | 2500 | 300 | unknown |
| model-3 | unknown | unknown | 2500 | 300 | unknown |

Notes:
- Full pass: 500 unique items × 5 conditions = 2500 requests per model.
- Noise extra: 30 items × 5 conditions × (3 repeats - 1) = 300 additional requests per model (repeat 1 counted in/alongside configured noise execution plan as applicable; planner reports extra repeats beyond first).
- Model-1 limits read from `configs/models.yaml` (`requests_per_minute: 20`, self-imposed throttle; `requests_per_day: 1000`, checked 2026-11-19). Days = ceil(total / min(RPD, RPM×1440)).
- Model-2 and model-3 remain **unknown** until their official limits/strings are filled in `configs/models.yaml`.
- The plan command was run against the working-tree items path at generation time; actual runs must use the agreed/final items file and respect gate checks (items hash sidecar, FROZEN.md for non-NU real runs, quotas/rate limits).
