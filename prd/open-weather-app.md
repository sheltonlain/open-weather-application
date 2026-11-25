# PRD: Open Weather App

## Problem Statement

People want fast, accurate, personalized weather information for where they are right now and for any other place in the world. Existing tools often make it hard to:

- tell apart places that share a name (e.g. "Paris, TX" vs. "Paris, France"),
- search by ZIP/postal code as easily as by city name,
- keep a personal list of frequently checked places and switch between them quickly,
- see weather in their preferred units (°C vs. °F) without re-configuring every visit,
- understand forecast trends at a glance, or see where a place is on a map.

Users also expect their data and the service's secrets to be handled safely.

## Solution

A web application where a user can:

- Register and log in to a personal account, and set a preferred temperature unit (Metric °C or Imperial °F) that is remembered.
- Search for any location by city name or ZIP/postal code from a single search box, and pick the correct place from a clear list of matches showing name, state, and country.
- Have their current location detected automatically when they have already granted browser permission, or with one click on "Use my location".
- See current conditions for the selected place: temperature, "feels like", humidity, wind speed, cloudiness, atmospheric pressure, and sunrise/sunset times.
- See a multi-day forecast as an interactive chart (daily highs/lows and conditions, with hover details).
- See the selected place on an interactive map with weather markers for the selected location and their saved favorites.
- Save locations as favorites from search results or the dashboard, switch between them instantly, and remove ones they no longer need. Each user's list is private to them.

The app is a single dashboard that updates in place (no full page reloads) as the user searches, switches locations, or manages favorites. All weather data is fetched by the server; the browser never sees the weather service's API key.

## User Stories

### Accounts & preferences
1. As a visitor, I want to register an account with a username and password, so that I can save my own favorites and preferences.
2. As a registered user, I want to log in and log out, so that my personal data is available only to me.
3. As a visitor, I want to see an error message when registration details are invalid (e.g. username taken, passwords don't match), so that I can correct them.
4. As a registered user, I want to choose Metric (°C, m/s) or Imperial (°F, mph) units in my settings, so that weather is shown the way I understand it.
5. As a registered user, I want my unit preference remembered across sessions and devices, so that I don't have to set it every time.
6. As an anonymous visitor, I want to see weather in Metric units by default and be able to switch units for my session, so that I can use the app without an account.
7. As a user, I want switching units to update the display instantly, so that I can compare values without waiting.

### Search & location discovery
8. As a user, I want to type a city name into a single search box, so that I can find weather for any city worldwide.
9. As a user, I want to type a ZIP/postal code into the same search box, so that I can find weather for a precise area without choosing a search mode.
10. As a user, I want a ZIP code without a country to default to the US, and to be able to add a country code (e.g. "10001,US" or "SW1A 1AA,GB"), so that I can search postal codes in other countries.
11. As a user, I want city search results shown as a list with name, state/region, and country, so that I can distinguish places with the same name (e.g. "Paris, TX, US" vs. "Paris, FR").
12. As a user, I want the result list shown even when there is only one match, so that I can confirm it's the place I meant.
13. As a user, I want a clear "no results found" message when a search matches nothing, so that I know to try a different query.
14. As a user, I want search results to appear without the page reloading, so that searching feels fast.
15. As a returning user who previously allowed location access, I want my current location detected automatically when I open the app, so that I see local weather immediately.
16. As a new user, I want a "Use my location" button rather than a surprise permission prompt, so that I stay in control of sharing my location.
17. As a user, I want to see the name of my detected location (not just coordinates), so that I know which place the weather is for.
18. As a user who denied location access, or whose device can't provide it, I want the app to fall back to my first favorite (if logged in) or the search box with a hint, so that I'm never stuck on an empty screen.

### Current weather
19. As a user, I want to see the current temperature and "feels like" temperature for the selected place, so that I know how to dress.
20. As a user, I want to see humidity, wind speed, cloudiness, and atmospheric pressure, so that I understand overall conditions.
21. As a user, I want to see sunrise and sunset times for the selected place, so that I can plan around daylight.
22. As a user, I want a weather condition description and icon, so that I can grasp conditions at a glance.
23. As a user, I want a friendly "weather unavailable, please try again" message if the weather service fails or is slow, so that the app doesn't break or hang.

### Forecast
24. As a user, I want a multi-day (5-day) forecast showing each day's high, low, and condition, so that I can plan ahead.
25. As a user, I want the forecast shown as an interactive chart where I can hover for exact values, so that I can see trends easily.
26. As a user, I want the forecast to use my preferred units, so that it's consistent with current conditions.

### Favorites
27. As a logged-in user, I want to save a location to my favorites directly from search results, so that I can find it again quickly.
28. As a logged-in user, I want to save the location I'm currently viewing from the dashboard, so that I can bookmark places I discover.
29. As a logged-in user, I want to see my list of favorites on the dashboard, so that I can switch between them with one click.
30. As a logged-in user, I want clicking a favorite to load its weather instantly without re-searching, so that quick-switching is effortless and always picks the exact place I saved.
31. As a logged-in user, I want to remove a favorite, so that my list stays relevant.
32. As a logged-in user, I want the app to prevent me from saving the same place twice, so that my list stays clean.
33. As a logged-in user, I want my favorites to be visible only to me, so that my saved places are private.
34. As an anonymous visitor, I want to be prompted to log in when I try to save a favorite, so that I understand why it's needed.

### Map
35. As a user, I want an interactive map centered on the selected location, so that I can see where it is.
36. As a user, I want the map to show a weather marker (temperature and icon) for the selected location, with a popup for details, so that I can read weather spatially.
37. As a logged-in user, I want my favorites to appear as weather markers on the map, so that I can compare places visually.
38. As a user, I want to pan and zoom the map, so that I can explore the surrounding area.

### Security & reliability
39. As a user, I want the weather service's API key never to be exposed in my browser, so that the service can't be abused and stays available.
40. As a user, I want repeated views of the same place within a short time to load quickly, so that switching between locations feels instant.
41. As a user, I want my session and form submissions protected against cross-site request forgery, so that other sites can't act on my behalf.

## Implementation Decisions

### Architecture
- Server-rendered Django application backed by SQLite, managed with uv.
- Frontend is Django templates styled with Tailwind CSS + DaisyUI (via django-tailwind-cli), with HTMX + django-htmx for partial page updates. No Node/npm build pipeline; Chart.js and Leaflet are loaded from a CDN at pinned versions.
- Three Django apps, one per group of stakeholder needs:
  - **accounts**: custom user model, registration, login/logout, unit settings.
  - **weather**: OpenWeather client service, unit conversion, search, current weather, forecast, and map data.
  - **favorites**: saved locations model and add/remove/list views.

### External weather API
- Use only the **free OpenWeather 2.5 tier**: current weather, 5-day/3-hour forecast, and Geocoding (direct by city name, by ZIP, and reverse).
- One Call 3.0 is not used (requires payment card). Therefore **UV index is out of scope** for now.
- All OpenWeather calls are made only from a dedicated weather service module on the backend. Views never call the external API directly. The browser communicates only with our backend.
- HTTP calls use `requests` with a ~5-second timeout. Network errors, timeouts, and non-success responses raise a single custom weather-service error, which views turn into a friendly message instead of a crash.
- Always request metric units from OpenWeather. Conversion to imperial (°C→°F, m/s→mph) is done in a small module of pure functions on our side, so one cached response serves all users and switching units needs no extra API call.
- The forecast's 3-hour steps are grouped into per-day high/low/condition by the weather service, so templates and charts receive clean daily data.

### Caching
- Django's built-in local-memory cache, 10-minute expiry, matching OpenWeather's update frequency.
- Cache key combines the endpoint with latitude/longitude rounded to 4 decimal places.

### Accounts & authentication
- Django session authentication (no JWT). Sessions are signed with the secret key loaded from the environment.
- Custom user model extending Django's abstract user with a `units` field (choices: metric, imperial; default metric). Configured before the first migration.
- Anonymous users default to metric; their unit choice is stored in the session.
- Pages: register, login, logout, and settings (unit preference). These are normal full pages.

### Favorites model
- One `Favorite` table holding a snapshot of the geocoded place: owning user, display name, state, country, latitude, longitude, created timestamp.
- Latitude/longitude rounded to 4 decimal places (about 11 m); unique constraint on (user, latitude, longitude) prevents duplicates.
- Favorites are always filtered by the current user; all favorite views require login. Attempts to act on another user's favorite return not-found.
- Selecting a favorite loads weather directly from its stored coordinates (no re-geocoding).

### Search behavior
- One search box. A pure query-parsing function decides the type: input starting with digits is treated as a ZIP/postal code (default country US unless a country code follows a comma); anything else is a city query.
- City queries return up to 5 matches from the direct geocoding endpoint; results are always shown as a list (name, state, country) with a save action per result.
- ZIP queries return a single place.
- Postcodes that begin with letters (e.g. UK) require an explicit country code.

### Geolocation
- On page load, a small script checks the browser Permissions API. If permission is already granted, coordinates are fetched silently and weather is loaded via HTMX. Otherwise a "Use my location" button is shown.
- On denial or error: fall back to the user's first favorite (if logged in) or show the search box with a hint.
- Coordinates are reverse-geocoded on the backend to produce a display name.

### Pages, URLs, and HTMX
- Single dashboard at the root with search, current weather, forecast chart, map, and favorites sidebar.
- HTMX partial endpoints, following RESTful methods and standard status codes:
  - search results: GET with a query parameter,
  - weather panel (current + forecast + map data): GET with latitude/longitude parameters,
  - add favorite: POST,
  - remove favorite: DELETE by id,
  - favorites list returned updated after add/remove.
- Each partial view also renders as a full page when the request is not an HTMX request, so direct links and refreshes work.
- CSRF token is sent on HTMX requests via a header configured once in the base template.

### Forecast chart
- Chart.js line chart of daily high/low with hover tooltips. Data is passed from the server to the page via Django's safe JSON-script mechanism. The chart re-initializes after HTMX swaps.

### Map
- Leaflet with OpenStreetMap base tiles (no key required).
- Weather markers for the selected location and the user's favorites, each with a popup of key details.
- OpenWeather weather tile overlays are **not** used, because their URLs embed the API key.

### Security
- All secrets (OpenWeather API key, Django secret key) are stored in a `.env` file at the project root, loaded at startup, and never committed. `.env` and the SQLite database are already in `.gitignore`.
- The API key must never appear in templates, JavaScript, page source, network requests from the browser, or URLs loaded by the browser.

### Testing strategy
- Test-driven development, feature by feature, with pytest + pytest-django; factory_boy for users and favorites.
- Tests never call the real network. All OpenWeather calls are mocked with the `responses` library using saved JSON fixtures; unexpected outbound calls fail the test.
- The cache is cleared automatically between tests.
- Good first TDD candidates: unit conversion functions, query parsing (city vs. ZIP, default country), forecast daily grouping, favorites uniqueness and per-user isolation, login-required behavior, and weather-service error handling.
- Ruff for linting and formatting; tests and lint must pass before each commit.

## Out of Scope

- UV index (requires One Call 3.0 or a second provider). It can be added later, e.g. via Open-Meteo, without changing the rest of the design.
- OpenWeather weather map overlays (clouds, precipitation, temperature tiles), including a backend tile proxy.
- Hourly forecast views beyond what's needed for daily grouping.
- Weather alerts, historical weather, and air-quality data.
- JWT/token authentication, social login, password reset by email, and email verification.
- Reordering, renaming, or grouping favorites.
- Persistent (database or Redis) caching.
- Native mobile apps, offline support, push notifications.
- Any JavaScript build tooling (Node, npm, bundlers) or SPA frameworks.
- Production deployment configuration.

## Further Notes

- The free OpenWeather tier allows about 60 calls/minute; the 10-minute cache keeps normal use well within that.
- The "such as" wording in the stakeholder metrics list allows omitting UV; this omission should be stated in the formal requirements document.
- These decisions are also summarized for AI coding assistants in the project's CLAUDE.md. The existing AGENTS.md describes an unrelated example project and should be updated or removed to avoid conflicting guidance.
