# Seantinel 🌊🛰️

**Seantinel** is an advanced geospatial monitoring and intelligence platform. It is engineered to automatically detect and flag illegal activities—specifically Illegal, Unreported, and Unregulated (IUU) fishing and "dark vessels" (ships intentionally disabling their tracking transponders to evade authorities). 

Primarily focused on the Black Sea region, Seantinel bridges the gap between real-time telemetry and advanced satellite imagery analysis to protect vulnerable marine ecosystems.

---

## 🎯 Business Case & Logistics

### The Problem
Marine Protected Areas (MPAs) such as *Rezervația Kaliakra*, *Gura Veleka*, and *Banca Koketrays* are ecologically vital but extremely difficult to police. Illicit vessels frequently enter these zones to fish illegally. When doing so, they turn off their **AIS (Automatic Identification System)** transponders, becoming invisible to standard radar and coast guard monitoring tools.

### The Solution (How Seantinel Works)
Seantinel solves this by fusing two entirely different data streams:
1. **Live AIS Telemetry:** Broadcasts from cooperative vessels, providing real-time positioning, speed, and course.
2. **Sentinel-1 SAR Imagery:** Copernicus Synthetic Aperture Radar (SAR) imagery, processed by AI, which detects physical metallic hulls on the water regardless of cloud cover, weather, or time of day.

### The Workflow (Logistics)
1. **Authentication:** Coast guard users log into their isolated, secure accounts.
2. **Live Monitoring:** The dashboard opens an interactive map showing live AIS ship traffic (🚢) in the Black Sea.
3. **Active Scanning:** Click **"Scanează Nave Suspecte"**. The backend pings an AI pipeline that analyzes recent SAR satellite imagery for physical ships.
4. **Correlation Engine:** The frontend algorithms instantly correlate the physical SAR detections (🟦) against the live AIS data and the geographic boundaries of the Protected Areas.
5. **Automated Triage:** 
    - *Illegal Confirmed:* If an AIS signal is found inside a restricted polygon, it is flagged automatically.
    - *In Investigation:* If a physical ship is found in a restricted zone by the satellite, but *no AIS signal exists* at those coordinates, it is flagged as a high-risk dark vessel.
6. **Reporting:** Generates a formalized `ScanReport` which indexes all detections for their specific account, allowing them to track investigations securely.

---

## 🏗️ Technical Architecture

Seantinel is built on a modern, asynchronous **Django (MVT)** stack, specifically optimized for real-time data ingestion and geospatial mapping.

### 1. Backend Framework & Database
- **Django 6.0+ & ASGI:** Upgraded to use Daphne/Channels, allowing Django to handle the asynchronous websocket loops required for live AIS ingestion.
- **Relational Data Modeling:** 
  - `CustomUser`: Expands standard auth to include Badge Numbers and Institutions.
  - `ScanReport`: A hierarchical model acting as a parent container for a batch scan. Detections are sequentially indexed (e.g., Report #1, Report #2) specific to each individual user to ensure strict **multi-tenant data isolation**.
  - `IllegalReport`: The child models containing specific vessel anomalies, coordinates, and confidence scores.

### 2. Live AIS Stream Pipeline
- Managed within `monitoring/ais_monitoring.py`.
- Uses Python `websockets` and `asyncio` to maintain a persistent connection to the `aisstream.io` API.
- Applies a strict geographic bounding box over the Black Sea to filter out global noise.
- Live vessel coordinates and historical polyline trails are cached directly in server memory, allowing Django to serve high-speed JSON endpoints to the frontend map without thrashing the database.

### 3. Frontend & Geospatial Engine
- **UI/UX:** Built with Bootstrap 5.3, fully localized in Romanian for regional accessibility, and featuring native `localStorage` Dark Mode toggling.
- **Leaflet.js:** The core interactive map engine. 
- **Layer Controls:** Users can dynamically toggle visibility between Live AIS data, Copernicus SAR data, and the GeoJSON restricted zones.
- **In-Browser Geometry Algorithms:** Instead of relying on heavy backend GIS databases (like PostGIS), the frontend JavaScript executes real-time spatial calculations:
  - *Point-in-Polygon (Ray Casting):* Determines if vessels breach complex geographical boundaries (e.g., Kaliakra).
  - *Haversine Formula:* Calculates spherical distances to determine if ships breach circular radius protections (e.g., 500m around river mouths).

### 4. Satellite AI Integration (Google Colab Tunnel)
- Heavy Computer Vision processing (OpenCV, CFAR algorithms, Rasterio) is offloaded to an external Jupyter/Colab pipeline. 
- Django communicates with this pipeline via a secure tunnel URL. When triggered, it requests the latest SAR anomaly coordinates and injects them alongside the mocked/live AIS data.

---

## 🚀 Setup & Installation

### 1. Prerequisites
Ensure you have Python 3.10+ and `git` installed.

### 2. Clone & Environment Setup
```bash
git clone https://github.com/mihnearafael/seantinel.git
cd seantinel

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the root directory. This is ignored by git for security.
```ini
# Django Cryptographic Key
SECRET_KEY=your_secure_django_key_here

# AIS API Key (Get from aisstream.io)
AISSTREAM_API_KEY=your_ais_api_key_here

# Colab AI Pipeline Tunnel (Ngrok/Localtunnel)
COLAB_API_URL=https://your-tunnel-url.loca.lt
```

### 5. Database Initialization
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Launch Platform
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/`. You will need to register an account to access the mapping dashboard.

---

## 📁 Repository Structure

```text
seantinel/
│
├── core/                   # Main Project Configuration
│   ├── settings.py         # App config, DB config, ASGI setup
│   └── asgi.py             # Entry point for ASGI (Daphne) server
│
├── monitoring/             # App: Real-Time Map & AIS Tracking
│   ├── ais_monitoring.py   # Async WebSocket client caching live AIS data
│   ├── views.py            # Serves JSON endpoints & AI pipeline trigger
│   └── urls.py             # Routing for dashboard map
│
├── reports/                # App: Incident Management System
│   ├── models.py           # Defines `ScanReport` and `IllegalReport` schemas
│   └── views.py            # Logic for report generation and investigation states
│
├── users/                  # App: Identity and Access Management (IAM)
│   ├── models.py           # CustomUser model extending AbstractUser
│   └── views.py            # Login, Logout, and Registration logic
│
├── templates/              # HTML Frontend Templates (Romanian / Dark Mode)
│   ├── base.html           # Main layout with navigation bar & theme toggle
│   ├── monitoring/         # Dashboard map (Leaflet + Geometry Algorithms)
│   └── reports/            # Report lists and vessel investigation templates
│
├── sat_pipeline/           # Standalone Jupyter Notebooks for SAR processing
├── requirements.txt        # Python dependencies
└── manage.py               # Django CLI management script
```