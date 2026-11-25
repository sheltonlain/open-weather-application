# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-11-24 — Phase 1: walking skeleton (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md Implement phase 1`
2. "yes, approved" (the three TDD behaviors: dashboard renders, missing secret fails startup, CSRF via `hx-headers`)
3. "python-dotenv (Recommended)" (answer to: how to load `.env`, since no dotenv package was in the stack)
4. "yes, approved" (cycle 1 RED test: `GET /` renders `weather/dashboard.html` extending `base.html`)
5. "yes, go ahead"
6. "yes, approved" (cycle 2 RED test: `require_env` raises `ImproperlyConfigured` naming the variable)
7. "yes, go ahead"
8. "yes, approved" (cycle 3 RED test: the page's `hx-headers` token passes Django's CSRF check on a POST)
9. "yes, go ahead" (finish the non-TDD parts of the phase)
10. "Do step 2 for me. I don't understand it. Explain how it works"
11. "the manual checks pass"
12. "Can these be easily determined by reading files in the codebase?" (about the proposed CLAUDE.md additions)
13. "yes, add just that one line"

### Summary
- **Outcome:** Django project (`config/`) with the `accounts`, `weather`, and `favorites` apps; custom `accounts.User` with `units` (default metric) as the first migration; secrets loaded from `.env` via python-dotenv and `config.env.require_env()`, which fails loudly when one is missing; `base.html` with Tailwind/daisyUI (django-tailwind-cli, plugin mode), HTMX via django-htmx's bundled script, and the CSRF `hx-headers`; placeholder dashboard at `/`. Test harness: `config/test_settings.py` with fake keys, autouse fixtures that clear the cache and block unmocked HTTP. 10 tests pass, Ruff clean, all Phase 1 criteria ticked. CLAUDE.md gained python-dotenv in the stack and one line about the shared `mocked_responses` fixture.
- **Deviations:** Asked a follow-up about adding python-dotenv (not in the approved stack); the recommended option was accepted. Asked Claude to do manual step 2 (create `.env`) and explain it; Claude generated `SECRET_KEY` but left the OpenWeather key as a placeholder for me to paste. Questioned whether the three proposed CLAUDE.md additions were discoverable from the code; trimmed them to the one non-obvious rule.
- **Sideways:** `require_env` started as a non-raising stub so the cycle 2 test could fail on an assertion; `makemigrations` ran against that stub with no `.env`, which only worked because the stub didn't raise yet. The empty-value branch of `require_env` (`SECRET_KEY=`) is implemented but has no test of its own. The CSRF test can't compare token strings (Django masks them per render), so it asserts a POST with the page's token isn't rejected with 403. Ruff auto-fixed 6 issues and reformatted Django's generated files. `requirements.md` was untracked before this session and was left out of the commit.

## 2026-11-24 — Grill-me design session, CLAUDE.md, and PRD

### Prompts
1. `/grill-me @project-idea.md`
2. "I will use OpenWeather API" (in answer to: which OpenWeather API: One Call 3.0, free 2.5, or 2.5 + separate UV source)
3. "I'll be using the free version"
4. "A, leave UV out for now"
5. "B" (three Django apps: accounts, weather, favorites)
6. "A" (Django session auth + custom User model with `units` field)
7. "A" (Favorite stores a place snapshot: name, state, country, lat, lon)
8. "B" (Django local-memory cache, 10-minute TTL)
9. "b" (always fetch metric, convert in Python)
10. "a" (Chart.js via CDN for the forecast)
11. "a" (Leaflet + OpenStreetMap, weather markers only, no OpenWeather tile overlays)
12. "c" (hybrid geolocation: auto if permission already granted, else "Use my location" button)
13. "a" (single search box; `parse_query()` treats leading digits as ZIP, default US)
14. "a" (`requests` + `responses` for mocking OpenWeather in tests)
15. "a" (single dashboard with HTMX partials; partials also render as full pages)
16. `/to-prd use this grill-me session to create the prd`
17. "commit this session to PROMPTS.md, commit, and push to github"

### Summary
- **Outcome:** 13 design decisions settled through the grill-me interview. Wrote `CLAUDE.md` (project overview, stack/commands, structure, 11 architecture decisions, testing rules, TDD steps, commit rules) and `prd/open-weather-app.md` (problem, solution, 41 user stories, implementation decisions, out of scope).
- **Deviations:** Overrode the recommendation of One Call 3.0 in favor of the free 2.5 tier, which led to dropping the UV index (recorded as out of scope). All other questions accepted the recommended option. The first answer ("I will use OpenWeather API") didn't pick an option, so I asked a follow-up explaining the free vs. One Call 3.0 tiers.
- **Sideways:** The grill-me skill only asks for an interview, but I also wrote `CLAUDE.md` at the end because `project-idea.md` asked for it. Two choices in `CLAUDE.md` were never discussed: the `config/` settings folder name and Python 3.12+. I flagged that `AGENTS.md` described an unrelated example project (Lost & Found); it was removed from the working tree before this commit.

