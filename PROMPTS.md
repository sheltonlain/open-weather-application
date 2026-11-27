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

## 2026-11-26 — Phase 10 follow-up: geolocation search-result race

### Prompts
1. "fix the search-result race in the geolocation script"
2. "manual verification passes, commit and push"
3. "Append a session log to PROMPTS.md and add necessary info to CLAUDE.md"

### Summary
- **Outcome:** fixed the known gap logged in the Phase 10 entry. The geolocation script in `templates/base.html` now listens for `htmx:beforeRequest` targeting `#weather-panel`; if any such request starts while the browser is still finding the position, the location result and the first-favorite fallback are ignored, so the user's choice wins. Clicking "Use my location" clears the flag, so an explicit request still replaces the current panel. Committed as `2dae10e` and pushed. CLAUDE.md gained a note on this rule.
- **Deviations:** none; I recommended the request-started check over comparing panel elements because it also covers a click whose response is still in flight, and the user accepted the fix as built.
- **Sideways:** nothing went wrong. The fix is browser-only JavaScript with no automated test (no JS runner); I held the commit until the user confirmed four manual checks (search during the permission prompt, favorite during the prompt then Block, button after picking, silent load on reload).

## 2026-11-26 — Phase 10: geolocation and fallback (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md implement phase 10`
2. "Yes, replace that test" (approved the three TDD behaviors: reverse-geocoded name, coordinates label on reverse-geocode failure, dashboard fallback to the first favorite; and replacing the old station-name test)
3. "yes, make it pass" (cycle 1 RED test: a panel without a name shows the reverse-geocoded name)
4. "yes, go ahead with cycle 2"
5. "yes, make it pass" (cycle 2 RED test: timeout / 500 / empty reverse result labels the weather with its coordinates)
6. "yes, go ahead with cycle 3"
7. "yes, make it pass" (cycle 3 RED test: `data-fallback-url` points at the first favorite only when there is one)
8. "yes, build the UI and script"
9. "in chrome, the app says access is blocked"
10. "the map i mean"
11. "manual verification passes. Proceed"
12. "yes, update CLAUDE.md and proceed"

### Summary
- **Outcome:** `weather.services.reverse_geocode()` (cached like other lat/lon calls) names panels loaded without a `name`; on failure or no result the panel is labeled with its coordinates instead of OpenWeather's station name. The dashboard gained `weather/partials/geolocation.html` (a "Use my location" button, a search hint, and `data-fallback-url` for the first favorite) and an inline script in `base.html` that auto-locates only when permission is already granted and otherwise falls back to the first favorite or the hint. Fixed a Phase 9 map bug: OSM served "Access blocked" tiles because Django's `same-origin` referrer policy sent no Referer; the tile layer now uses `referrerPolicy: "strict-origin-when-cross-origin"`. CLAUDE.md gained notes on the geolocation data attributes, place labeling, the OSM referrer policy, and mocking `/geo/1.0/reverse`. 160 tests pass.
- **Deviations:** the user approved replacing `test_panel_without_a_name_falls_back_to_openweather_name`, since Phase 10 changes that requirement. Three cache tests were repaired to mock the reverse endpoint, and the forecast cache test now expects 3 first-render calls instead of 2.
- **Sideways:** the cycle 1 test first used the wrong fake API key (`test-api-key` instead of `test-openweather-key`), fixed mechanically. A scripted edit inserted the reverse mock into the wrong test in `tests/test_forecast.py`; caught by a still-failing call count and moved into `mock_new_york`. During manual verification the user reported "access is blocked"; I first assumed it was Chrome's location permission and gave Windows/Chrome settings advice before the user clarified it was the map, which led to the OSM Referer fix. The browser script has no automated tests (no JS runner); its behavior was confirmed manually. Known gap: a silent location lookup that finishes after the user picks a search result can replace the panel.

## 2026-11-26 — Phase 9: map with selected and favorite markers (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md implement phase 9`
2. "Yes" (the three TDD behaviors: selected marker data in the active units, favorite markers only for the current user, one failing favorite doesn't break the map)
3. "yes, make it pass" (cycle 1 RED test: the selected marker's JSON for an imperial user)
4. "yes, go ahead with cycle 2"
5. "yes, make it pass" (cycle 2 RED test: only Alice's favorites, none for anonymous)
6. "yes, go ahead with cycle 3"
7. "yes, keep the marker and make it pass" (cycle 3 RED test: a failed favorite keeps a marker with `temp: None`)
8. "yes, go ahead with the rest of the phase"
9. "when I switch to farenheit, the map does not load"
10. "manual verification passed, go ahead with the acceptance criteria"
11. "Yes" (add two CLAUDE.md lines, then PROMPTS.md, commit, and push)

### Summary
- **Outcome:** The weather panel now includes a Leaflet 1.9.4 map (pinned CDN with SRI hashes, OpenStreetMap tiles, no OpenWeather overlays). `weather/views.py` builds `map_data` (emitted via `json_script` as `weather-map-data`): a selected marker (label, lat/lon, temp, emoji, description, humidity, wind, unit labels, all in the active units) and markers for the logged-in user's favorites, read through `request.user.favorites` with weather from the cached service. A favorite whose weather fails keeps a `{label, lat, lon, temp: None}` marker; a favorite at the selected spot is skipped; no map or favorite calls when the selected weather fails. `drawWeatherMap()` in `base.html` draws DaisyUI badge markers and `textContent`-built popups, on load and after HTMX swaps, leaving the map alone on unrelated swaps. New `tests/test_map.py` (7 tests); 156 pass, Ruff clean, all Phase 9 criteria ticked. CLAUDE.md §5.9 and §5.10 each gained a line.
- **Deviations:** Claude asked whether a favorite with failed weather should keep its marker or be dropped, recommending keeping it; I chose to keep it. The weather view reading `request.user.favorites` stretched CLAUDE.md's "in templates" wording; Claude flagged it up front and the wording was updated at the end.
- **Sideways:** Cycle 3 first crashed with an exception instead of failing an assertion; the test switched to `Client(raise_request_exception=False)` and checked the status before parsing (mechanical, assertions unchanged). The cache test first failed because the forecast was unmocked and retried; it now mocks the forecast. Manual verification found the map blank (no tiles) after switching to °F on the dashboard. Claude reproduced it in headless Edge over CDP: HTMX's attribute settling on the id-matched `#weather-map` stripped Leaflet's classes when the units toggle's `afterSettle` drew the map inside the panel's settle window. The fix was to drop the id and use `data-weather-map`; the two selector tests were updated. The forecast canvas still uses an id and wasn't changed. `requirements.md` is still untracked.

## 2026-11-26 — Phase 8 follow-up: save a pending favorite after login

### Prompts
1. "is there a way to make it so that when you click save and then login, you are redirected to the search you had done. Or for the city to automatically appear in the list?"
2. "Do option 1" (save the pending favorite automatically after login, rather than option 2, pushing search URLs so login returns to the results)
3. "yes, push it"
4. "add this session to PROMPTS.md"

### Summary
- **Outcome:** An anonymous Save is now finished after login or registration. `login_required_htmx` validates the anonymous POST with `FavoriteForm` and keeps the cleaned data in the session under `pending_favorite`. A `user_logged_in` receiver in the new `favorites/signals.py` (connected in `FavoritesConfig.ready()`) pops it, saves it, and adds a "Saved …" or "already in your favorites" message. The rounding plus `get_or_create` logic moved out of the add view into a shared `save_favorite()` in the new `favorites/services.py`, along with `saved_message()` and the duplicate message, so the view and the receiver share one path. 5 new tests (login, register, existing favorite not duplicated, pending save used only once, invalid save not kept); 149 tests pass, Ruff clean. Committed as `9f7f704 feat(favorites): save a pending favorite after login` and pushed.
- **Deviations:** Claude offered two options (auto-save after login; `hx-push-url` so login returns to the search) and recommended option 1; I chose option 1. Option 2 was not built. The login still returns to `/`, not the search results.
- **Sideways:** The message helpers first lived in `signals.py`, and the views imported them from there; they were moved to `services.py` while still green. `test_pending_save_is_used_once` failed on its first run because the first login's "Saved …" message was never displayed (no `follow=True`) and appeared on the second login; the test was fixed to follow the first redirect, and the assertions were unchanged. Claude committed under CLAUDE.md §9 but waited for my go-ahead before pushing. `requirements.md` is still untracked.

## 2026-11-26 — Phase 8: favorites (save, list, switch, remove) (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md implement phase 8`
2. "yes, go ahead" (the three TDD behaviors: duplicate save rejected cleanly after 4-decimal rounding, another user's favorite returns 404 on delete, anonymous HTMX save gets a login prompt)
3. "yes, keep 200 and make it pass" (cycle 1 RED test; keep 200 rather than 409 for a duplicate save)
4. "yes, make it pass" (cycle 2 RED test: deleting another user's favorite returns 404 and keeps it)
5. "yes, go ahead with cycle 3"
6. "yes, make it pass" (cycle 3 RED test: anonymous HTMX save returns `HX-Redirect` to `/accounts/login/?next=/`)
7. "yes, go ahead with the rest of the phase"
8. "manual verification passed, go ahead with the acceptance criteria"
9. "yes, add both, then commit and push" (two CLAUDE.md lines)

### Summary
- **Outcome:** `favorites.Favorite` model and migration (4-decimal `DecimalField` lat/lon, `UniqueConstraint` on `(user, lat, lon)`, a `place` property that returns a `weather.services.Place`), `FavoriteForm`, admin registration, and `FavoriteFactory`. `POST /favorites/` rounds coordinates and uses `get_or_create`: 201 plus the updated list for a new place, 200 with "already in your favorites" for a duplicate, 400 for invalid input, and a redirect with a message when not HTMX. `GET /favorites/` returns the list partial or a full page. `DELETE /favorites/<id>/` uses `get_object_or_404(..., user=request.user)`. A new `login_required_htmx` decorator sends anonymous HTMX requests to login via `HX-Redirect`, with `next` taken from `HX-Current-URL`. A shared `favorites/partials/sidebar.html` is included on the dashboard, search, and weather pages; Save buttons appear on every search result and on the weather panel, whose context now passes `place` instead of `place_label`. New `tests/test_favorites.py` (21 tests). 144 tests pass, Ruff clean, all Phase 8 criteria ticked. CLAUDE.md §5.9 gained two lines (the HTMX login decorator; the sidebar include and the rule that `weather` reads favorites only through templates).
- **Deviations:** Claude flagged the 200-vs-409 choice for duplicates (HTMX 2 doesn't swap 4xx); kept 200 as recommended. All other recommendations were accepted.
- **Sideways:** Cycle 1's first draft would have crashed with an `IntegrityError` rather than failing an assertion, so the test uses `Client(raise_request_exception=False)` to make a 500 show up as a status code. Adding a `class` to the search-result `<li>` broke four existing tests that count bare `<li>` tags; the layout moved to an inner `div` instead of changing those tests. A bash heredoc for the regular tests failed on quoting, and the tests were written with the Edit tool instead. An invalid save (400) shows nothing in the sidebar because HTMX doesn't swap 4xx; accepted, since the hidden fields come from server data. `requirements.md` is still untracked and was left out of the commit.

## 2026-11-26 — Phase 7: 5-day forecast chart (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md Implement phase 7`
2. "yes, go ahead" (the three TDD behaviors: daily grouping from a saved fixture, grouping by local date not UTC, a forecast failure doesn't break current conditions; plus the "most frequent condition" rule)
3. "yes, go ahead" (cycle 1 RED test: the New York fixture becomes five `DailyForecast` days with exact highs, lows, conditions and daytime icons)
4. "go with (a)" (keep behavior 2 as an explicit test even though cycle 1 already forced local grouping, so it would pass straight away)
5. "yes, go ahead" (cycle 3 RED test: forecast 500 still shows current conditions plus "Forecast is unavailable right now. Please try again.")
6. "yes, go ahead" (build the rest of the phase: unit conversion, `json_script` chart data, Chart.js, HTMX re-init, regular tests)
7. "yes, everything works, go ahead" (manual verification steps all passed)
8. "can these be easily determined by reading the codebase?" (about the proposed CLAUDE.md additions)
9. "yes, add that line and go ahead"

### Summary
- **Outcome:** `weather/services.py` gained `DailyForecast` (with `emoji` and `in_units()`), a shared `icon_emoji()` helper, and `get_daily_forecast()`. It fetches `/data/2.5/forecast` through the existing 10-minute cache, groups 3-hour steps by the place's local date (`city.timezone`), keeps 5 days, and takes high/low from `main.temp`, the most frequent description as the condition, and its daytime icon. The weather panel fetches the forecast in its own `try` block, so a failure shows a friendly message under intact current conditions. The panel shows five day cards and a Chart.js 4.4.1 line chart (pinned jsDelivr URL in `base.html`) fed by `json_script` in the active units. One `drawForecastChart()` in `base.html` runs on `DOMContentLoaded` and `htmx:afterSettle`, destroying the old chart first. New `tests/test_forecast.py` (8 tests) and fixture `tests/fixtures/forecast_new_york.json`. 123 tests pass, Ruff clean, all Phase 7 criteria ticked. CLAUDE.md §6 gained one line: an unmocked forecast silently renders the "unavailable" branch instead of failing a test.
- **Deviations:** Chose option (a) for behavior 2, a characterization test, after Claude pointed out it couldn't go RED. Questioned whether the proposed CLAUDE.md additions were discoverable from the code; kept only the non-obvious testing line.
- **Sideways:** Cycle 1's fixture already crossed local midnight, so local-date grouping was needed to pass it and behavior 2 couldn't be true red-green. To show the test still checks the rule, Claude briefly switched the code to UTC grouping (both tests failed) and restored it. Claude's hand-computed timestamps for the behavior 2 test were off by 2 hours, and the test failed until they were fixed (mechanical repair, the assertion unchanged). Before approval of cycle 3, Claude removed a `response.context` assertion as an implementation detail. Wiring the forecast into the view broke two unit-switch cache tests that asserted exactly one HTTP call; they now mock both endpoints and compare call counts before and after the switch. Chart labels first used `%d` ("01 Dec"), which didn't match the cards ("1 Dec"), and were aligned. The fixture was generated by a throwaway script in the scratchpad, not committed. `requirements.md` is still untracked and was left out of the commit.

## 2026-11-26 — Phase 6: units preference (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md Implement phase 6`
2. "Yes" (the three TDD behaviors: conversion helpers, the panel renders in the active units, switching units saves the choice and makes no new OpenWeather call)
3. "yes" (cycle 1 RED test: `celsius_to_fahrenheit` and `ms_to_mph` tables, including -40 and 0)
4. "yes" (move on to cycle 2)
5. "yes" (cycle 2 RED test: an imperial user, logged in or via the session, sees 44°F / 38°F / 10.3 mph and no °C or m/s)
6. "yes" (move on to cycle 3)
7. "yes" (cycle 3 RED tests: switching to imperial saves `User.units` or `session["units"]`, and the re-rendered panel makes only one HTTP call in total)
8. "yes" (build the rest of the phase: header toggle, panel reload, settings page, regular tests)
9. "yes" (manual verification steps all passed)
10. "yes" (add the two proposed lines on active units and switching to CLAUDE.md)

### Summary
- **Outcome:** New pure module `weather/units.py` (°C→°F, m/s→mph, unit labels, session key). `CurrentWeather.in_units()` converts the cached metric data for display, so switching never calls OpenWeather again. `weather.views.active_units()` picks the user setting, then the session, then metric, and a new context processor exposes it to every template. New `POST /accounts/units/` (`set_units`) validates the value (400 if unknown), requires POST and a CSRF token, and saves to `User.units` or the session. For HTMX it re-renders the header °C/°F toggle and sends `HX-Trigger: unitsChanged`; otherwise it shows a "Units saved." message and redirects to a same-site `next` URL. The weather panel listens for `unitsChanged` and re-fetches its own URL. New login-required settings page at `/accounts/settings/`, a Settings link in the header, and message display in `base.html`. 115 tests pass, Ruff clean, all Phase 6 criteria ticked. CLAUDE.md now documents the active-units and switching patterns.
- **Deviations:** None. I accepted every recommendation. Claude chose to have the settings page post to the same `set_units` endpoint instead of having its own form view, and to have the toggle endpoint return the re-rendered toggle (200) instead of the 204 it described during cycle 3; neither was raised with me.
- **Sideways:** In cycle 3 the anonymous test first failed with a `KeyError` instead of an assertion; switched to `session.get(...)` (mechanical repair, noted before approval). A scripted string replacement in `accounts/views.py` didn't match after Ruff reformatting and also clipped a line; it was caught by inspecting the file and fixed by hand. One new settings-page test first matched the header toggle's `value="imperial"` instead of the radio button and was fixed to target the radio. `requirements.md` is still untracked and was left out of the commit.

## 2026-11-26 — Phase 5: current weather panel (TDD)

### Prompts
1. `/implement @prd/open-weather-app.md @plans/open-weather-app.md Implement phase 5`
2. "yes, approved" (the three TDD behaviors: sunrise/sunset in local time, repeated requests served from the cache, missing/invalid lat/lon returns 400)
3. "Yes" (cycle 1 RED test: New York panel shows sunrise 06:55 and sunset 16:31, not the UTC 11:55/21:31)
4. "Yes" (move on to cycle 2)
5. "Yes" (cycle 2 RED test: two calls for coordinates that round to the same 4 decimals make one HTTP call)
6. "Yes" (move on to cycle 3)
7. "Yes" (cycle 3 RED test: 6 parametrized bad-coordinate cases return 400 with no OpenWeather call)
8. "Yes" (build the rest of the phase: search results link to the panel, remaining view/service tests)
9. "New york displays the name Weehawken, US"
10. "Yes, all pass"
11. "yes, add just #1" (the CLAUDE.md line about weather links carrying the place name)

### Summary
- **Outcome:** `weather/services.py` gained `CurrentWeather` (with an `emoji` property mapping OpenWeather icon codes), `get_current_weather()`, `_local_time()` (applies OpenWeather's `timezone` offset), and `_get_cached_json()` (local-memory cache of the raw metric JSON for 10 minutes, key = endpoint + lat/lon rounded to 4 decimals; failures are not cached). `Place` gained `label` and `query_string`. New view `GET /weather/?lat=&lon=` validates coordinates (missing, non-numeric, NaN, out of range → 400 before any API call), shows a friendly message on service failure, and renders the partial for HTMX or the full page otherwise. New templates `partials/weather_panel.html` and `weather.html`; the dashboard includes the empty panel, and each search result is now a link with `hx-get` into `#weather-panel`. New fixture `weather_new_york.json` and `WEATHER_URL` helper. 82 tests pass, Ruff clean, all Phase 5 criteria ticked. CLAUDE.md now says weather links carry `name`/`state`/`country` because OpenWeather names its nearest station.
- **Deviations:** Claude chose emoji icons instead of OpenWeather icon images, because Phase 9 forbids OpenWeather URLs in the page or browser requests; I didn't object. Of four proposed CLAUDE.md additions I kept only the place-name rule.
- **Sideways:** Manual testing showed "Weehawken, US" for New York: `/data/2.5/weather` labels coordinates with its nearest station. The fixture had used a made-up "New York" name, which hid the problem in tests. Fixed by passing the chosen name through the panel links (with a test that fails on the station name, written first) and making the fixture realistic; three non-TDD tests were updated for the rename and the longer link. Cycle 3 needed scaffolding first, because the initial view crashed (`KeyError`/`ValueError`) instead of failing on an assertion. Ruff flagged one long line and reformatted one file. DST limitation noted but not fixed: sunrise uses OpenWeather's current offset, so it can be an hour off on a changeover day. `requirements.md` is still untracked and was left out of the commit.

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

