# Plan: Open Weather App

> Source PRD: `prd/open-weather-app.md`

## Architectural decisions

Durable decisions that apply across all phases:

- **Owning apps**: `accounts` (custom user, register/login/logout, unit settings), `weather` (OpenWeather client, unit conversion, search, current weather, forecast, map data), `favorites` (saved locations).
- **URLs**:
  - `/` (dashboard: search, weather panel, forecast chart, map, favorites sidebar)
  - `GET /weather/search/?q=` (search results partial)
  - `GET /weather/?lat=&lon=` (weather panel partial: current, forecast, map data)
  - `POST /favorites/` (add favorite, returns the updated list)
  - `DELETE /favorites/<id>/` (remove favorite by pk, returns the updated list)
  - Register, login, logout, and settings pages under `accounts` (full pages)
  - Every partial view also renders a full page when the request is not `request.htmx`.
- **Models**:
  - `accounts.User(AbstractUser)` with `units` (`metric` | `imperial`, default `metric`). `AUTH_USER_MODEL` is set before the first migration.
  - `favorites.Favorite(user FK, name, state, country, lat, lon, created_at)`: lat/lon rounded to 4 decimals, unique on `(user, lat, lon)`.
- **Auth**: Django session auth. Favorites views require login and every query is scoped to `request.user`; another user's favorite returns 404. Anonymous units are stored in the session (default metric).
- **External API boundary**: only `weather/services.py` talks to OpenWeather (free 2.5 endpoints only), using `requests`, a 5s timeout, and `WeatherServiceError` on failure. Always fetch `units=metric` and convert in the pure functions in `weather/units.py`.
- **Caching**: local-memory cache, 10 min TTL, key = endpoint + lat/lon rounded to 4 decimals.
- **Secrets**: `OPENWEATHER_API_KEY` and `SECRET_KEY` come from `.env` and startup fails if either is missing. The key never reaches the browser.
- **Frontend**: Django templates, HTMX + django-htmx, Tailwind + DaisyUI via django-tailwind-cli, and Chart.js + Leaflet from CDN at pinned versions. The CSRF header is set via `hx-headers` in `base.html`.
- **Testing**: pytest + pytest-django, factory_boy, `responses` with JSON fixtures in `tests/fixtures/`. Unmocked HTTP fails the test, the cache is cleared automatically between tests, and tests use a fake API key.

---

## Phase 1: Walking skeleton

**User stories**: 39, 41

### What to build

A running Django project with the three apps, the custom `User` model (with `units`) migrated as the first migration, settings that load secrets from `.env` and fail loudly if they're missing, a `base.html` that loads HTMX, Tailwind/DaisyUI, and the CSRF `hx-headers`, and an empty dashboard at `/`. The test harness is in place: pytest-django, a fake API key setting, an autouse cache-clear fixture, and outbound HTTP blocked by default.

### Acceptance criteria

- [x] `GET /` returns 200 and renders the dashboard shell extending `base.html`
- [x] `AUTH_USER_MODEL` points to `accounts.User` with a `units` field defaulting to `metric`
- [x] Startup fails with a clear error if `OPENWEATHER_API_KEY` or `SECRET_KEY` is missing
- [x] `.env.example` exists with placeholder values only; `.env` and `db.sqlite3` stay gitignored
- [x] `base.html` sends the CSRF token on HTMX requests via `hx-headers`
- [x] `uv run pytest` and Ruff pass

---

## Phase 2: Register, login, logout

**User stories**: 1, 2, 3

### What to build

Full-page registration, login, and logout. The dashboard header shows the logged-in username with a logout action, or login/register links for anonymous visitors.

### Acceptance criteria

- [x] A visitor can register with a username and password and is logged in afterwards
- [x] Invalid registrations (username taken, mismatched passwords) re-render with errors
- [x] A user can log in and log out; logout uses POST
- [x] The header reflects the authentication state

---

## Phase 3: City search to results list

**User stories**: 8, 11, 12, 13, 14

### What to build

A single search box on the dashboard that sends `GET /weather/search/?q=` via HTMX. The service calls `/geo/1.0/direct` (limit 5) and the partial renders a list of name, state, and country, even for a single match, or a "no results found" message. Service failures show a friendly message.

### Acceptance criteria

- [x] A city query calls `/geo/1.0/direct` with the expected params (asserted via `responses`)
- [x] Results render as a list with name, state, and country; one match still renders as a list
- [x] An empty result shows "no results found"; a blank query is handled gracefully
- [x] A timeout, non-200 response, or malformed JSON raises `WeatherServiceError` and shows a friendly message
- [x] An HTMX request returns the partial; a non-HTMX request returns the full page

---

## Phase 4: ZIP search in the same box

**User stories**: 9, 10

### What to build

`parse_query()` (pure) classifies input that starts with digits as a ZIP, defaulting the country to `US`, and also accepts an explicit `,CC` country code. Anything else is treated as a city. ZIP queries call `/geo/1.0/zip` and render as a one-item results list.

### Acceptance criteria

- [x] `parse_query()` unit tests: city, bare ZIP to US, ZIP with a country code, whitespace handling
- [x] A ZIP search calls `/geo/1.0/zip` with `zip=<code>,<country>`
- [x] A ZIP that isn't found shows "no results found"
- [x] A letter-first postcode with a country code (e.g. `SW1A 1AA,GB`) is documented as needing the country and handled per the PRD

---

## Phase 5: Current weather panel

**User stories**: 19, 20, 21, 22, 23, 40

### What to build

`GET /weather/?lat=&lon=` renders the weather panel: place name, condition description and icon, temperature, feels like, humidity, wind speed, cloudiness, pressure, and sunrise/sunset in the location's local time. Clicking a search result loads the panel via HTMX. Responses are cached for 10 minutes, keyed by endpoint and rounded lat/lon.

### Acceptance criteria

- [x] The panel shows every listed metric from a saved `/data/2.5/weather` fixture
- [x] Sunrise and sunset are shown in the location's local time (using the timezone offset)
- [x] Missing or invalid lat/lon returns 400
- [x] A service failure renders a friendly "weather unavailable, please try again" message
- [x] A second request for the same rounded coordinates within the TTL makes no new HTTP call
- [x] The rendered page and partial never contain the API key

---

## Phase 6: Units preference

**User stories**: 4, 5, 6, 7

### What to build

Pure conversion functions (°C to °F, m/s to mph). A settings page lets logged-in users persist `units`. Anonymous visitors get a units toggle stored in the session. The weather panel renders in the active units, and switching re-renders the panel via HTMX without any new OpenWeather call (served from the cache).

### Acceptance criteria

- [x] Conversion helpers are unit-tested, including edge values
- [x] A logged-in user's choice persists on `User.units` across sessions
- [x] An anonymous visitor defaults to metric, and their toggle is stored in the session
- [x] The weather panel shows the correct values and unit labels for each setting
- [x] Switching units doesn't trigger an outbound HTTP call when the data is cached

---

## Phase 7: 5-day forecast chart

**User stories**: 24, 25, 26

### What to build

The service fetches `/data/2.5/forecast` and groups 3-hour steps into daily high/low/condition. The weather panel includes a Chart.js line chart of the daily highs and lows with hover tooltips, fed via `json_script`, converted to the active units, and re-initialized after HTMX swaps.

### Acceptance criteria

- [x] Daily grouping is unit-tested against a saved forecast fixture (correct days, highs, lows, condition)
- [x] Days are grouped by the location's local date, not UTC
- [x] Chart data is emitted via `json_script` in the active units
- [x] The chart renders on full-page loads and after HTMX swaps
- [x] A forecast failure shows a friendly message without breaking current conditions

---

## Phase 8: Favorites (save, list, switch, remove)

**User stories**: 27, 28, 29, 30, 31, 32, 33, 34

### What to build

The `Favorite` model and migration. `POST /favorites/` saves a place from a search result or from the current dashboard location and returns the updated sidebar list. The sidebar lists the user's favorites; clicking one loads `/weather/?lat=&lon=` from its stored coordinates (no re-geocoding). `DELETE /favorites/<id>/` removes one and returns the updated list. Anonymous visitors who try to save are prompted to log in.

### Acceptance criteria

- [ ] lat/lon are rounded to 4 decimals; a duplicate `(user, lat, lon)` is rejected cleanly (no 500), with clear feedback
- [ ] Adding returns 201 (or the updated list partial) and the sidebar updates via HTMX
- [ ] Clicking a favorite loads its weather from the stored coordinates
- [ ] Deleting removes it and returns the updated list; another user's favorite returns 404
- [ ] All favorites views require login; an anonymous HTMX save gets a login prompt instead of a broken swap
- [ ] Lists and lookups are always scoped to `request.user` (tested with two users via factory_boy)
- [ ] POST/DELETE without a CSRF token are rejected

---

## Phase 9: Map with selected and favorite markers

**User stories**: 35, 36, 37, 38

### What to build

A Leaflet map with OpenStreetMap tiles in the weather panel, centered on the selected location with a weather marker (temperature and icon) and a details popup. Logged-in users also see markers for each favorite with their current weather. Marker data is passed via `json_script`, and the map re-initializes after HTMX swaps. No OpenWeather tile overlays.

### Acceptance criteria

- [ ] The map centers on the selected location and supports pan/zoom
- [ ] The selected marker shows the temperature and icon, and its popup shows key details in the active units
- [ ] Favorites appear as markers for logged-in users only, and only that user's favorites
- [ ] Favorite weather uses the cached service; a failure for one favorite doesn't break the map
- [ ] No OpenWeather URLs or API key appear in the page source or browser requests

---

## Phase 10: Geolocation and fallback

**User stories**: 15, 16, 17, 18

### What to build

On dashboard load, a small inline script checks the Permissions API. If geolocation permission is already granted, it fetches coordinates silently and loads the weather panel via HTMX. Otherwise it shows a "Use my location" button. The backend reverse-geocodes the coordinates via `/geo/1.0/reverse` to produce the displayed place name. If permission is denied or there's an error, it falls back to the user's first favorite or shows the search box with a hint.

### Acceptance criteria

- [ ] The weather panel shows a reverse-geocoded place name for coordinates without a known name
- [ ] A reverse-geocode failure still shows the weather, labeled with the coordinates
- [ ] With no granted permission, the button is shown and no permission prompt appears on load
- [ ] The fallback loads the first favorite for logged-in users who have one; otherwise the search hint shows
