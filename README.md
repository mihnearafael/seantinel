# SeaNtinel 🌊🛰️

Seantinel is an advanced geospatial monitoring and intelligence platform designed to detect illegal maritime activities, such as illicit fishing and "dark vessels" (ships that have intentionally disabled their transponders). Primarily focused on the Black Sea region, the platform correlates real-time **AIS (Automatic Identification System)** data streams with AI-driven **Satellite Imagery Analysis** (Sentinel-1 SAR) to identify and flag suspicious behaviors, particularly within marine protected areas.

---

## 🏗️ Architecture (Top-Down)

Seantinel is built on a modern **Django + ASGI** stack, blending traditional server-side rendering with asynchronous processing for real-time data ingestion.

### 1. Web Framework (Django MVT)
- **Models (M):** Defines the relational database schema. Features custom users, geographical polygons for protected areas, and hierarchical incident management (`ScanReport` containing multiple `IllegalReport` vessels). (Defaults to SQLite for easy setup).
- **Views (V):** Contains the business logic. Renders interactive maps using Folium, processes API requests for real-time data, handles report generation and state transitions, and enforces data isolation per officer.
- **Templates (T):** Responsive frontend built with HTML and Bootstrap 5.3 (featuring native Dark Mode and fully localized in Romanian), heavily utilizing `django-crispy-forms`.

### 2. Real-Time AIS Stream (Asynchronous)
- Utilizing Python's `asyncio` and `websockets` libraries, the backend maintains a persistent connection to the `aisstream.io` API.
- Position reports are filtered via a geographic bounding box specifically covering the Black Sea.
- Live vessel coordinates and historical trail data are stored in server memory dictionaries, allowing the Django endpoints to serve JSON data to the frontend map rapidly.

### 3. Satellite Data & AI Pipeline
- The system integrates computer vision and satellite imagery using libraries like `opencv-python`, `rasterio`, and `sentinelhub`.
- **Concept:** By downloading Sentinel-1 Synthetic Aperture Radar (SAR) imagery, the AI pipeline detects physical vessels on the water (even through cloud cover or at night). It cross-references these physical detections with the live AIS data. If a vessel is seen by the satellite but is *not* broadcasting an AIS signal, it is flagged as a "Dark Vessel".
- **Current Integration:** The Django app triggers a mock pipeline/Google Colab tunnel (`/monitoring/scan/`) that simulates this computationally heavy AI process, generating dynamic localized `ScanReport` batches on the map for demonstration.

---

## 🚀 Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mihnearafael/seantinel.git
   cd seantinel
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables (`.env`):**
   Create a `.env` file in the root directory and add the following keys (ensure this is ignored via `.gitignore`):
   ```ini
   SECRET_KEY=your_django_secret_key
   AISSTREAM_API_KEY=your_aisstream_api_key
   COLAB_API_URL=your_ngrok_or_localtunnel_url
   ```

5. **Apply Migrations & Run Server:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```

---

## 📁 Project Structure & File Interoperability

```text
seantinel/
│
├── core/                   # Main Project Configuration
│   ├── settings.py         # App configuration, DB config, Auth models, ASGI setup
│   ├── urls.py             # Root URL routing, delegates to app-specific urls.py
│   ├── asgi.py & wsgi.py   # Entry points for ASGI (Daphne/Channels) & WSGI servers
│
├── monitoring/             # App: Real-Time Map & AIS Tracking
│   ├── ais_monitoring.py   # Async WebSocket client fetching live AIS data in background
│   ├── views.py            # Serves Dashboard map (Folium), JSON endpoints & mock pipeline
│   ├── urls.py             # Routes for dashboard (/), vessels JSON, and scan trigger
│
├── reports/                # App: Incident Management System
│   ├── models.py           # Defines `ScanReport` and `IllegalReport` schemas
│   ├── views.py            # Logic for generating reports and updating incident statuses
│   ├── urls.py             # Routes for viewing (/reports/) and resolving alerts
│
├── users/                  # App: Identity and Access Management (IAM)
│   ├── models.py           # CustomUser model extending AbstractUser (adds institution/badge)
│   ├── views.py            # Login, Logout, Profile and Registration logic
│   ├── urls.py             # Auth endpoints (/users/login/, etc.)
│   ├── forms.py            # CustomUserCreationForm logic
│
├── templates/              # HTML Frontend Templates (Romanian / Dark Mode capable)
│   ├── base.html           # Main layout with navigation bar & theme toggle
│   ├── monitoring/         # Dashboard map template
│   ├── reports/            # Report lists and details templates
│   └── users/              # Authentication templates
│
├── sat_pipeline/           # Standalone Jupyter Notebooks for Satellite SAR processing
├── requirements.txt        # Python dependencies list
└── manage.py               # Django CLI management script
```

---

## 🔌 How URLs, Views, and Files Work Together

The flow of data and user interaction in Seantinel is highly interconnected:

1. **Dashboard Rendering (`/` -> `monitoring/urls.py` -> `monitoring.views.dashboard_map`)**:
   - When a user visits the site, Django calls `dashboard_map`.
   - The view queries the database for `ProtectedArea` models, extracting their `geometry_json` to draw green ecological polygons.
   - It queries `IllegalReport` models to place markers on the map. Red markers signify "CONFIRMED" illegal activity, while orange signifies "UNCONFIRMED" or "INVESTIGATING".
   - The Python `folium` library compiles this into raw HTML/JS Leaflet map code, which is passed as context to the `dashboard.html` template.

2. **Live Map Updates (`/monitoring/vessels/` & `/monitoring/trails/`)**:
   - While the user views the dashboard, background JavaScript queries these two endpoints.
   - These views return raw JSON data straight from the `vessels` and `history` dictionaries actively managed by the background `ais_monitoring.py` websocket loop.

3. **Scanning for Threats (`/monitoring/scan/`)**:
   - An authority clicks "Scan Region" on the frontend.
   - A POST request is sent to `trigger_mock_pipeline` in `monitoring/views.py`.
   - The view randomly generates coordinates within the Black Sea, creates a new `IllegalReport` in the database, attaches a success message, and redirects the user back to the dashboard, instantly displaying the new threat.

4. **Incident Resolution (`/reports/`)**:
   - Only accessible to logged-in authorities (`@login_required`).
   - The user visits a specific report (`/reports/<id>/`), handled by `report_detail` in `reports/views.py`.
   - The user reviews the details (coordinates, AI confidence score, ship name) and submits a form to change the status (e.g., from `UNCONFIRMED` to `CONFIRMED`).
   - The view saves the model change to the database. The next time the dashboard loads, the map marker color will reflect this new status.

---

## 🛠️ Technology Stack Details

### Backend & Framework
- **Django 5.0+**: Provides the robust ORM, security, routing, and administrative backends.
- **Django Channels & Daphne (ASGI)**: Upgrades Django to handle asynchronous connections required for continuous WebSockets.
- **python-dotenv**: Safely manages environment variables like the Django `SECRET_KEY` and the `AISSTREAM_API_KEY`.

### Application Features (Auth & Forms)
- **Custom Authentication**: Instead of Django's default user, Seantinel uses a `CustomUser` model (in `users/models.py`). This mandates custom fields critical for authorities: `institution_name` and `badge_number`.
- **django-crispy-forms & crispy-bootstrap5**: Used to render forms elegantly and responsively in the frontend templates without writing complex HTML boilerplate.

### Geospatial & Mapping
- **Folium**: Bridges Python and Leaflet.js. Allows the backend to construct rich, interactive maps with tooltips, custom icons, and GeoJSON overlays purely in Python before sending them to the browser.
- **GeoPandas & Shapely**: Included for complex manipulation, intersection checking, and processing of geographical data polygons (Protected Areas).

### Real-Time Data Integration
- **websockets**: Async Python client used to ingest continuous NMEA data streams.
- **aisstream.io API**: Provides the global real-time ship positioning data, filtered down via bounding boxes directly in the stream subscription message.

### AI & Satellite Processing (Data Science Stack)
- **SentinelHub API**: Used to programmatically fetch Sentinel-1 SAR imagery.
- **Rasterio**: Used to read and interpret complex multi-band GeoTIFF satellite files.
- **OpenCV (opencv-python-headless)**: Applies computer vision techniques (thresholding, contouring) to the SAR imagery to isolate high-reflection anomalies representing metallic ship hulls.
- **Pandas**: Used for data frame manipulation, aggregating detections, and comparing them against known AIS data sets.
