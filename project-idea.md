Based on the following information, help me create CLAUDE.md to outline the project, tech stack, and key architecture decisions for the project. This file should be short, to the point, and should not be verbose. Reference AGENTS.md for an example.

1. Project Background & System Description
You are tasked with engineering a weather web application from initial requirements to AI-assisted coding and testing.
High-Level Problem Statement
Users need fast, accurate, and personalized weather insights for their current location as well as any searched location worldwide. The goal of this project is to guide you through the entire software engineering lifecycle: extracting formal requirements from business needs, designing architecture with UML diagrams, establishing AI steering rules (AGENTS.md), and developing a secure, fully tested full-stack web application.
Core Application Capabilities (Stakeholder Needs)
User Identity: Users can register a new account for login. 
Users must be able to configure preferred temperature units (Metric °C vs. Imperial °F).
Geocoding & Location Discovery: Search locations by city name or ZIP/postal code. The system must distinguish multi-match queries (e.g., "Paris, TX" vs. "Paris, France") and automatically detect current device coordinates when permitted.
Current Weather & Metrics: Real-time atmospheric conditions (such as temperature, "feels like", humidity, wind speed, UV index, cloudiness, atmospheric pressure, and sunrise/sunset times).
Forecasts: Multi-day forecast trends with interactive visualizations.
Bookmarking & Saved Locations: Saving frequent locations ("favorites") directly from search results or the active dashboard, with quick-switching access and list management. Each user has their own list.
Interactive Map View: An embedded interactive map (like OpenStreetMap) displaying the selected area and weather markers.


Please adhere to the following basic security requirements:
Environment Variables (.env):
All secret keys, such as OPENWEATHER_API_KEY, database connection strings, and authentication secrets (JWT secrets/session salts), must be stored in a .env file at the root of your project.
Version Control Safety (.gitignore):
The .env file must never be committed to git. You must add .env to your .gitignore.
Backend Key Isolation (Zero Client-Side Leaks):
The OpenWeather API key must never be exposed in client-side code, network headers, or browser bundles.
All calls to external weather APIs must be proxied through your backend server. The client only communicates with your backend API.


## Tech stack

- Python, Django, SQLite
- Package/environment manager: **uv**
- Tailwind CSS + DaisyUI via django-tailwind-cli
- HTMX + django-htmx for partial page updates
- Ruff (lint + format), pytest + pytest-django + factory_boy (tests)