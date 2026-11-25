# CLAUDE.md

## 1. Project Overview
Open Weather App: an educational Django web app giving users current weather, multi-day forecasts, a map, and per-user saved locations for their current position or any searched place worldwide. Keep code simple and readable for students.

## 2. Tech Stack & Commands
- **Backend:** Python 3.12+, Django, SQLite (`db.sqlite3`)
- **Frontend:** Django templates, HTMX + django-htmx, Tailwind CSS + DaisyUI via django-tailwind-cli. Chart.js and Leaflet from CDN (pinned versions). No Node/npm.
- **Weather data:** OpenWeather **free 2.5 APIs** only: `/data/2.5/weather`, `/data/2.5/forecast`, `/geo/1.0/direct`, `/geo/1.0/zip`, `/geo/1.0/reverse`. No One Call 3.0, so **no UV index**.
- **HTTP:** `requests`. **Tests:** pytest, pytest-django, factory_boy, `responses`. **Lint/format:** Ruff.
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
weather/           # services.py (OpenWeather client), units.py, search/weather views
favorites/         # Favorite model, add/remove/list views
templates/         # base.html + per-app full pages and partials/
tests/             # pytest files + fixtures/ (saved OpenWeather JSON)
```

## 4. Architecture Decisions
1. **Security:** All secrets (`OPENWEATHER_API_KEY`, `SECRET_KEY`) live in `.env` (gitignored). The browser only talks to our backend; the API key must never appear in templates, JS, or browser-visible URLs. Never use OpenWeather tile URLs in the browser.
2. **Auth:** Django session auth with custom `accounts.User(AbstractUser)` and a `units` field (`metric`/`imperial`). Set `AUTH_USER_MODEL` before the first migration. Anonymous users default to metric (stored in session).
3. **OpenWeather client:** All external calls go through `weather/services.py`; views never call the API directly. Use a 5s timeout; raise `WeatherServiceError` on failure and show a friendly message.
4. **Units:** Always fetch `units=metric`; convert to imperial in `weather/units.py` (pure functions).
5. **Caching:** Django local-memory cache, 10 min TTL, key = endpoint + lat/lon rounded to 4 decimals.
6. **Search:** One box. `parse_query()` treats input starting with digits as ZIP (default country `US`, e.g. `10001,US`); otherwise city via `/geo/1.0/direct`. Always show results as a list (name, state, country) with a save button.
7. **Geolocation:** If browser permission is already granted, auto-detect; else show a "Use my location" button. Fallback: first favorite or the search box. Reverse-geocode on the backend.
8. **Forecast:** Group 3-hour steps into daily high/low/condition in `services.py`; render with Chart.js via `json_script`.
9. **Map:** Leaflet + OpenStreetMap tiles with weather markers (selected location + favorites). No weather tile overlays.
10. **Favorites:** `Favorite(user, name, state, country, lat, lon, created_at)`; lat/lon rounded to 4 decimals; unique per `(user, lat, lon)`. Each user sees only their own list; views require login.
11. **Pages & HTMX:** `/` dashboard with HTMX partials: `GET /weather/search/?q=`, `GET /weather/?lat=&lon=`, `POST /favorites/`, `DELETE /favorites/<id>/`. Partial views also render full pages when not `request.htmx`. Send CSRF token via `hx-headers` in `base.html`. Use correct HTTP methods and status codes.

## 5. Testing Rules
- Tests never hit the real network. Mock every OpenWeather call with `responses` and JSON fixtures in `tests/fixtures/`.
- Clear the cache between tests (autouse fixture).
- Use factory_boy for users and favorites.

## 6. Implementation Strategy (TDD)
Work feature by feature:
1. Write failing tests in `tests/` (behavior, validation, status codes).
2. Run `uv run pytest` and confirm they fail.
3. Implement the minimal models/services/views to pass.
4. Run `uv run pytest` and `uv run ruff check .`; both must pass.
5. Build the template/HTMX UI for the feature.

## 7. Git Commit Directives
After a step passes tests and lint:
- Stage only relevant files (`git add <files>`). Never commit `.env` or `db.sqlite3`.
- Conventional commits: `git commit -m "<type>(<scope>): <short description>"`, e.g. `feat(favorites): add remove favorite endpoint`.
- Report the commit message and hash.
