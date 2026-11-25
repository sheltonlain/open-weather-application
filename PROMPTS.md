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

