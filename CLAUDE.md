# CLAUDE.md

## 1. Project Overview
Open Weather App: an educational Django web app giving users current weather, multi-day forecasts, a map, and per-user saved locations for their current position or any searched place worldwide. Keep code simple and readable for students. Requirements: `prd/open-weather-app.md`.

## 2. Tech Stack & Commands
- **Backend:** Python 3.12+, Django, SQLite (`db.sqlite3`)
- **Frontend:** Django templates, HTMX + django-htmx, Tailwind CSS + DaisyUI via django-tailwind-cli. Chart.js and Leaflet from CDN (pinned versions). No Node/npm.
- **Weather data:** OpenWeather **free 2.5 APIs** only: `/data/2.5/weather`, `/data/2.5/forecast`, `/geo/1.0/direct`, `/geo/1.0/zip`, `/geo/1.0/reverse`. No One Call 3.0, so **no UV index**.
- **HTTP:** `requests`. **Config:** `python-dotenv` (loads `.env`). **Tests:** pytest, pytest-django, factory_boy, `responses`. **Lint/format:** Ruff.
- **Package manager:** `uv`
  - Add package: `uv add <package>` (dev: `uv add --dev <package>`)
  - Run server + Tailwind watcher: `uv run python manage.py tailwind runserver`
  - Migrations: `uv run python manage.py makemigrations && uv run python manage.py migrate`
  - Tests: `uv run pytest`
  - Lint/format: `uv run ruff check . --fix && uv run ruff format .`

## 3. Project Structure
```
config/            # settings, root urls
accounts/          # custom User (units field), register/login/settings
weather/           # services.py (OpenWeather client), units.py, queries.py (parse_query), search/weather views
favorites/         # Favorite model, add/remove/list views
templates/         # base.html + per-app full pages and partials/
tests/             # pytest files + fixtures/ (saved OpenWeather JSON)
```

## 4. Dependency Rules
- **Layering (one direction only):** templates ← views → services/forms/models. Views orchestrate; business logic lives in services or pure helper modules.
- **Only `weather/services.py` talks to OpenWeather.** No other module imports `requests` or builds OpenWeather URLs.
- Models never call services or external APIs. Pure helpers (`weather/units.py`, `weather/queries.py::parse_query()`) have no Django or network imports.
- `favorites` may import from `weather` services; `weather` must not import from `favorites` or `accounts` models (read `request.user` only).
- **Packages:** add only with `uv add`. Do not add packages beyond the stack above without asking. Never add Node/npm, bundlers, or SPA frameworks. Never commit hand-edited lockfiles.

## 5. Architecture Decisions
1. **Auth:** Django session auth with custom `accounts.User(AbstractUser)` and a `units` field (`metric`/`imperial`). Set `AUTH_USER_MODEL` before the first migration. Anonymous users default to metric (stored in session).
2. **OpenWeather client:** Use a 5s timeout; raise `WeatherServiceError` on failure and show a friendly message.
3. **Units:** Always fetch `units=metric`; convert to imperial in `weather/units.py` (pure functions).
   - **Active units:** `weather.views.active_units(request)` (user setting → session → metric); every template gets it as `active_units`. Convert for display with `CurrentWeather.in_units(units)` and label with `TEMP_LABELS`/`SPEED_LABELS` from `weather/units.py`. Never re-fetch data to change units.
   - **Switching:** `POST /accounts/units/` saves the choice and fires the HTMX event `unitsChanged`. Any panel showing unit-dependent values listens with `hx-trigger="unitsChanged from:body"` and re-fetches its own URL.
4. **Caching:** Django local-memory cache, 10 min TTL, key = endpoint + lat/lon rounded to 4 decimals.
5. **Search:** One box. `parse_query()` treats input starting with digits as ZIP (default country `US`, e.g. `10001,US`); a letter-first postcode is a ZIP only with a 2-letter country code (e.g. `SW1A 1AA,GB`); otherwise city via `/geo/1.0/direct`. ZIPs use `/geo/1.0/zip`; its 404 means "no results", not a service error. Always show results as a list (name, state, country) with a save button.
6. **Geolocation:** If browser permission is already granted, auto-detect; else show a "Use my location" button. Fallback: first favorite or the search box. Reverse-geocode on the backend.
   - The inline script in `base.html` reads `data-geolocation`, `data-weather-url` and `data-fallback-url` (first favorite's panel URL) from `weather/partials/geolocation.html`.
   - A panel request without `name` is labeled by `/geo/1.0/reverse`, else by its coordinates; never by OpenWeather's station name.
7. **Forecast:** Group 3-hour steps into daily high/low/condition in `services.py`; render with Chart.js via `json_script`.
8. **Map:** Leaflet + OpenStreetMap tiles with weather markers (selected location + favorites). No weather tile overlays.
   - Keep `referrerPolicy: "strict-origin-when-cross-origin"` on the OSM tile layer: Django's default `same-origin` policy sends no Referer, and OSM then serves "Access blocked" tiles.
9. **Favorites:** `Favorite(user, name, state, country, lat, lon, created_at)`; lat/lon rounded to 4 decimals; unique per `(user, lat, lon)`. Always filter by `request.user`; views require login.
   - Protect favorites views with `favorites.views.login_required_htmx`, not plain `login_required`: a 302 makes HTMX swap the login page into the sidebar, so anonymous HTMX requests get `HX-Redirect` to login instead.
   - Save buttons target `#favorites-list`, so every page that shows one must include `favorites/partials/sidebar.html`. `weather` reads favorites only via `user.favorites` (in templates, or `request.user.favorites` in views, e.g. map markers), never by importing the model.
10. **Pages & HTMX:** `/` dashboard with HTMX partials: `GET /weather/search/?q=`, `GET /weather/?lat=&lon=`, `POST /favorites/`, `DELETE /favorites/<id>/`. Partial views also render full pages when not `request.htmx`. Send CSRF token via `hx-headers` in `base.html`. Use correct HTTP methods and status codes. Weather panel links carry `name`/`state`/`country` too (build them with `Place.query_string`): OpenWeather's `/data/2.5/weather` `name` is its nearest station, not the chosen place.
   - JS widgets inside swapped panels (e.g. the Leaflet map) find their container by a `data-*` attribute, not an `id`: HTMX "settles" attributes of id-matched elements after a swap, stripping classes the library added.

## 6. Testing Seams & Mocking
- **Why:** the suite must run fully offline, fast, and without consuming live OpenWeather quota or needing the real API key.
- **Seam:** `weather/services.py` is the single boundary to the outside world. Mock at the HTTP layer with `responses` so the real service code (URL building, params, parsing, error handling) is exercised.
- Use saved JSON fixtures in `tests/fixtures/`. Assert the expected URL/params were called. Any unmocked outbound call must fail the test.
- The autouse `mocked_responses` fixture (`tests/conftest.py`) already blocks real HTTP; register OpenWeather mocks on it rather than opening another `responses.RequestsMock`.
- Test views by mocking HTTP the same way, or by patching the service function when only view behavior matters.
- Cover failure paths: timeout, non-200, malformed JSON → `WeatherServiceError` → friendly message.
- Tests use a fake key via settings override, never the real one. Clear the cache between tests (autouse fixture). Use factory_boy for users and favorites.
- Test users come from `tests/factories.py::UserFactory`; their password is `DEFAULT_PASSWORD`.
- Shared OpenWeather test helpers (`load_fixture`, endpoint URL constants) live in `tests/openweather.py`; reuse them instead of redefining per test file.
- A panel request without `name` also calls `/geo/1.0/reverse` (`GEO_REVERSE_URL`); mock it in cache/call-count tests too.
- The weather panel calls both `/data/2.5/weather` and `/data/2.5/forecast`. An unmocked forecast does not fail a test; it silently renders the "forecast unavailable" branch. Mock both when the forecast matters, and in cache tests compare call counts before and after a render rather than asserting a fixed number.

## 7. TDD Protocol (Red → Green → Refactor)
Work in thin vertical slices: one behavior at a time, end to end.
1. **Red:** write one small failing test for the next behavior (incl. validation and status codes). Run `uv run pytest` and confirm it fails for the expected reason.
2. **Green:** write the minimum code to make it pass. No extra features. Run `uv run pytest`; all tests pass.
3. **Refactor:** clean up names and duplication in code and tests with tests staying green. Run `uv run ruff check . --fix && uv run ruff format .`.
4. Repeat for the next behavior. Build the template/HTMX UI once the slice's backend is green.
Never write implementation before a failing test, and never weaken or delete a test to make it pass.

## 8. Security Guardrails & Code Style
**Security**
- Never hardcode secrets (API keys, `SECRET_KEY`, passwords) in code, settings, templates, tests, or docs. Load them from `.env` at startup (`OPENWEATHER_API_KEY`, `SECRET_KEY`); fail loudly if missing.
- `.env` and `db.sqlite3` stay in `.gitignore` and are never committed. Keep a `.env.example` with placeholder values only.
- The API key must never reach the browser: not in templates, JS, page source, browser network requests, or browser-loaded URLs. Never use OpenWeather tile URLs client-side.
- Keep CSRF protection on; require login for user data; scope every favorites query to `request.user`. Never log secrets or full API URLs containing the key.

**Code style**
- Ruff is the source of truth (format + lint, default 88-char lines); code must pass before commit.
- PEP 8 naming: `snake_case` functions/variables, `PascalCase` classes, `UPPER_CASE` constants.
- Type hints on service and helper functions; a one-line docstring on public functions.
- Small, focused functions; prefer clarity over cleverness. No `print()` in app code.
- Templates: Tailwind/DaisyUI classes only, no inline `<style>`; keep JS minimal and inline in templates.

## 9. Git Commit Directives
After a slice passes tests and lint:
- Stage only relevant files (`git add <files>`). Never commit `.env` or `db.sqlite3`.
- Conventional commits: `git commit -m "<type>(<scope>): <short description>"`, e.g. `feat(favorites): add remove favorite endpoint`.
- Report the commit message and hash.
