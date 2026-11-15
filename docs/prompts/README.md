# Antigravity prompts: how to use

Files in this folder:

| File | Who | When |
|---|---|---|
| `00_SESSION_START.md` | everyone | first message of **every** Antigravity session |
| `A_day1_data.md` | Sudais (Role A) | Day 1, hours 2 to 10 |
| `B_day1_eval.md` | Zia (Role B) | Day 1, hours 2 to 10 |
| `C_day1_analysis.md` | Younas (Role C) | Day 1, hours 2 to 10 |

## Before you start (Gate G0, hours 0 to 2; humans, not agents)
1. Zia: the repository must contain `AGENTS.md`, `.gitignore` (real name, with the dot), `.env.example`, `requirements.txt`, `configs/`, and the empty folders. Protect `main`.
2. Agree and write down in `docs/RULES.md` section 1 and `configs/config.yaml`: seed, helper LLM, RT tool, spot-check size, number of options per item.
3. Zia fills `configs/models.yaml` from each provider's **current** free-tier page (model strings and limits, with the date). Agents must never guess these.
4. Every person creates their own API key(s), puts them in a local `.env`, and checks they work with one tiny request.
5. Confirm the roles. Swap now if skills fit better; update `AGENTS.md` and `README.md` if you do.

## During the day
- Open the repo folder in Antigravity. Paste `00_SESSION_START.md` (with your role filled in), then paste your role's Day 1 file, **one task at a time**.
- Always ask for the **plan first**; read it; correct it; then let the agent implement.
- Work on your branch. After each task: run `pytest`, read the diff, run on a tiny sample, open a small PR, and have someone else review.
- A and B and C must not wait for each other: B builds on mock items and C on synthetic data until A commits the real sample.

## Humans own the science
Spelling conventions, review of Roman Urdu variants, interpretation of results and every citation are human work. Agents write code; people check it.
