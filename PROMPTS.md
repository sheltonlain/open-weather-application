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

## 2026-11-25 — Phase 4: ZIP search in the same box (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md Implement phase 4`
2. "Yes" (the three TDD behaviors: `parse_query()` classifies city vs. ZIP, `search_zip()` calls `/geo/1.0/zip` and treats 404 as no results, the search view routes ZIPs; plus the letter-first postcode rule: a ZIP only with a 2-letter country code)
3. "Yes, implement it" (cycle 1 RED test: `parse_query` table of 9 cases)
4. "yes, move on to behavior 2"
5. "Yes, implement it" (cycle 2a RED test: `search_zip("10001,US")` calls `/geo/1.0/zip` and returns one `Place`)
6. "Yes, implement it" (cycle 2b RED test: a 404 from `/geo/1.0/zip` returns `[]`)
7. "yes, move on to behavior 3"
8. "Yes, implement it" (cycle 3 RED test: searching `10001` lists one place, "New York, US")
9. "yes, go ahead with these" (unknown-ZIP and letter-first view tests, ZIP-aware placeholder and hint text)
10. "5 results in sw1a 1aa,gb and does not say london. Also pressing enter in the search box does not query the results. You have to physically press search"
11. "Enter works now, go with option A"
12. "yes, update CLAUDE.md then commit and push"

### Summary
- **Outcome:** New pure module `weather/queries.py` with `ParsedQuery` and `parse_query()`: digit-first input is a ZIP (default `US`), a letter-first postcode is a ZIP only with a 2-letter country code, and everything else is a city. `weather/services.py` gained `search_zip()` and a `NotFoundError` subclass of `WeatherServiceError`, raised by `_get_json` on a 404, so an unknown ZIP shows "No results found" instead of the outage message. The search view routes via `parse_query()`. The search box placeholder, aria-label, and blank-query hint now mention ZIPs and the country-code rule; `autocomplete="off"` was added to the input. New fixture `geo_zip_10001.json` and `GEO_ZIP_URL` helper; the failure test now runs against both lookups. 59 tests pass, Ruff clean, all Phase 4 criteria ticked. CLAUDE.md now records the letter-first rule, the ZIP 404 handling, and where `parse_query()` lives.
- **Deviations:** Claude proposed the letter-first postcode rule because the PRD's "digits first means ZIP" rule alone would have sent `SW1A 1AA,GB` to city search, breaking user story 10; I approved it. For the UK postcode label I chose option A: keep OpenWeather's postcode-as-name ("SW1A 1AA, GB") and leave proper names to Phase 10's reverse geocoding, rather than adding a reverse-geocode call now.
- **Sideways:** Cycle 1 first failed with `NotImplementedError` rather than an assertion, so the stub was changed to return a placeholder. Cycle 2b's RED was a raised `WeatherServiceError`, not an assertion failure; Claude flagged this and kept it, since it was the real wrong behavior rather than missing scaffolding. Manual step 5 wrongly promised that `SW1A 1AA,GB` would show "London"; calling the real API showed OpenWeather names full UK postcodes after the postcode itself. The "5 results" I reported could not be reproduced on the server (the real view returned one item); Claude's best explanation was the browser's autofill dropdown on the `type="search"` input, which would also explain Enter not submitting. Adding `autocomplete="off"` fixed Enter, but the root cause was never confirmed. Ruff reformatted one long test line. `requirements.md` is still untracked and was left out of the commit.

## 2026-11-25 — Phase 3: city search to results list (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md Implement phase 3`
2. "yes, approved" (the three TDD behaviors: city query calls `/geo/1.0/direct` and returns places, failures raise `WeatherServiceError`, HTMX gets the partial and other requests the full page)
3. "yes, approved" (cycle 1 RED test: `search_cities("London")` calls direct geocoding with `q`, `limit=5`, `appid` and returns `Place` objects)
4. "yes, go ahead"
5. "yes, approved" (cycle 2 RED test: timeout, non-200, and malformed JSON each raise `WeatherServiceError`)
6. "yes, go ahead"
7. "yes, approved" (cycle 3 RED test: an HTMX request to `/weather/search/` renders only the results partial)
8. "yes, go ahead" (finish the non-TDD parts of the phase)
9. "In 6, I do not see a result without the state"
10. "Step 6 generates the following list: Paris, Ile-de-France, FR"
11. "Sorry, step 6 actually returns: Paris, Ile-de-France, FR"
12. "Sorry, step 6 actually returns Paris, Ile-de-France, FR / Paris, Ile-de-France, FR / Parus, Texas, US"
13. "yes, add the duplicate removal test-first"
14. "yes, approved" (RED test: duplicate name/state/country results are dropped, keeping the first)
15. "the manual checks pass"
16. "yes, add just that one line" (CLAUDE.md: shared OpenWeather test helpers in `tests/openweather.py`)

### Summary
- **Outcome:** `weather/services.py` with a `Place` dataclass, `WeatherServiceError`, a shared `_get_json` helper (API key from settings, 5s timeout, `raise_for_status`, errors re-raised `from None` so the key-bearing URL never reaches tracebacks), and `search_cities` (limit 5, missing `state` tolerated, duplicates removed). `GET /weather/search/?q=` view returning the results partial for HTMX and a full page otherwise; a blank query shows a hint without calling OpenWeather; service failures show a friendly message (status 200 so HTMX swaps it). Search form and results partials included on the dashboard and the full search page. Fixtures for London, Paris, and Paris TX; shared helpers in `tests/openweather.py`. 42 tests pass, Ruff clean, all Phase 3 criteria ticked. CLAUDE.md gained one line about `tests/openweather.py`.
- **Deviations:** The full-page test for cycle 3 passed against the scaffolding stub, so it was kept as a normal regression test rather than a TDD cycle (same rule as phase 2). Save buttons on results were deferred to phase 8. Duplicate removal was not in the plan; it was added test-first after manual testing exposed it.
- **Sideways:** Manual step 6 wrongly promised that "Paris" would show a result without a state; OpenWeather returns "Ile-de-France". Claude corrected the instructions and pointed to the automated test for the no-state case. Several rounds of correcting the reported step 6 output then revealed OpenWeather returning the same Paris twice with slightly different coordinates, which the fixtures had not covered; this led to the duplicate-removal cycle. `requirements.md` is still untracked and was left out of the commit.

## 2026-11-25 — Phase 2: register, login, logout (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md implement phase 2`
2. "yes, approved" (the three TDD behaviors: valid registration logs in, invalid registration re-renders with errors, logout only via POST)
3. "yes, approved" (cycle 1 RED test: a valid registration POST creates the user, logs them in, and redirects to the dashboard)
4. "if its not a genuine red, let's group it with the normal tests"
5. "in 4, I don't see an error. Just a blank screen."
6. "the manual checks pass"
7. "yes, add just that one line" (CLAUDE.md: `UserFactory` and `DEFAULT_PASSWORD`)

### Summary
- **Outcome:** `RegisterForm` (on `UserCreationForm`) and a `register` view that logs the new user in and redirects to `/`; login and logout from Django's built-in `LoginView`/`LogoutView` under `/accounts/`; `LOGIN_URL`, `LOGIN_REDIRECT_URL`, and `LOGOUT_REDIRECT_URL` settings; register/login templates sharing a DaisyUI form-fields partial; a header showing the username and a POST logout button, or login/register links. Added `tests/factories.py::UserFactory` and 12 tests in `tests/test_accounts.py`. 22 tests pass, Ruff clean, all Phase 2 criteria ticked. CLAUDE.md gained one line about `UserFactory`/`DEFAULT_PASSWORD`.
- **Deviations:** Only cycle 1 ran as true TDD. Claude flagged that the invalid-registration test would pass immediately (the view already re-renders a bound invalid form); I chose to move it into the normal tests. Claude applied the same rule to the logout test, since Django's `LogoutView` already rejects GET with 405.
- **Sideways:** The manual step 4 instructions promised a "405 error page", but Django's 405 has an empty body, so the browser showed a blank screen. Claude explained how to confirm the 405 status in DevTools or with curl; no code change was made. The `login` route was added early as scaffolding because the register template links to it. `requirements.md` is still untracked and was left out of the commit.

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

