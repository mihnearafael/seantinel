import json
import random
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.conf import settings

import folium
from reports.models import ProtectedArea, IllegalReport
from .ais_monitoring import API_KEY, vessels, history

# =========================================================
# UTILITIES / ENVIRONMENT TESTS
# =========================================================
def test_env():
    if API_KEY:
        print(f"AIS KEY: {API_KEY[:4]}...")
    else:
        print("AIS KEY: Not set")

test_env()


# =========================================================
# AIS & MAP DASHBOARD VIEWS
# =========================================================
@login_required
def vessels_view(request):
    return JsonResponse(list(vessels.values()), safe=False)


@login_required
def trails_view(request):
    return JsonResponse(history)


@login_required
def dashboard_map(request):
    active_alerts = 0
    return render(request, 'monitoring/dashboard.html', {'active_alerts': active_alerts})


# =========================================================
# LOCAL VS CODE (.IPYNB) SATELLITE PIPELINE INTEGRATION
# =========================================================

@login_required
def proxy_map_image(request):
    """
    Fetches the generated radar image bounding boxes directly from 
    the local Flask server running inside your VS Code notebook.
    """
    # Fallback to localhost port 6184 if not specified in settings.py
    local_server_url = getattr(settings, 'LOCAL_FLASK_SERVER_URL', 'http://127.0.0.1:6184')
    
    try:
        res = requests.get(f"{local_server_url}/api/map-image", timeout=15)
        return HttpResponse(res.content, content_type=res.headers.get('Content-Type', 'image/png'))
    except Exception as e:
        print(f"❌ Error proxying local map image: {e}")
        return HttpResponse(status=500)


@login_required
def trigger_mock_pipeline(request):
    """
    Triggers the Sentinel-1 vessel detection engine executing locally 
    inside your VS Code Python Notebook environment.
    """
    if request.method == 'POST':
        local_server_url = getattr(settings, 'LOCAL_FLASK_SERVER_URL', 'http://127.0.0.1:6184')
        
        # Pull datetime from frontend request parameters if provided, otherwise default
        target_date = request.GET.get('datetime', '2026-04-25T12:00')
        scan_endpoint = f"{local_server_url}/api/scan?datetime={target_date}"
        
        try:
            print(f"📡 Requesting local VS Code pipeline: {scan_endpoint}")
            res = requests.get(scan_endpoint, timeout=120)
            
            print(f"--- Local Server Logs ---")
            print("STATUS CODE:", res.status_code)
            print("CONTENT TYPE:", res.headers.get("Content-Type"))
            
            if res.status_code != 200:
                return JsonResponse({
                    "success": False,
                    "message": f"Local server error: {res.status_code}",
                    "raw": res.text[:300]
                })

            try:
                data = res.json()
            except Exception:
                return JsonResponse({
                    "success": False,
                    "message": "Invalid JSON response received from local notebook app",
                    "raw": res.text[:300]
                })

            if data.get("success"):
                ships = data.get("ships", [])
                
                # Inject explicit overlaps with the mocked AIS data
                ships.extend([
                    {"lat": 43.1957483333333, "lon": 27.9097683333333, "confidence": 99.9},
                    {"lat": 42.85, "lon": 28.2, "confidence": 98.5},
                    {"lat": 43.35, "lon": 28.46, "confidence": 97.2},  # Overlaps Kaliakra + AIS
                    {"lat": 42.60, "lon": 27.65, "confidence": 94.0}   # Overlaps Koketrays (SAR only, no AIS)
                ])

                return JsonResponse({
                    "success": True, 
                    "message": f"Scanned Sentinel-1 Data locally. Found {len(ships)} dark vessels!",
                    "ships": ships,
                    "image_url": "/monitoring/proxy-map-image/"  # Maps to proxy_map_image view above
                })
            else:
                return JsonResponse({
                    "success": False, 
                    "message": data.get("message", "Unknown script error inside your notebook execution loop.")
                })

        except requests.exceptions.ConnectionError:
            return JsonResponse({
                "success": False,
                "message": f"Could not connect to VS Code. Ensure your .ipynb notebook server is actively running at {local_server_url}"
            })
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
            
    return JsonResponse({"success": False, "message": "Invalid method"})








# from django.shortcuts import render, redirect
# from django.contrib import messages
# import folium
# import random
# from reports.models import ProtectedArea, IllegalReport

# from django.http import JsonResponse
# from .ais_monitoring import API_KEY, vessels, history

# from django.contrib.auth.decorators import login_required

# @login_required
# def vessels_view(request):
#     return JsonResponse(list(vessels.values()), safe=False)

# def test_env():
#     if API_KEY:
#         print(f"AIS KEY: {API_KEY[:4]}...")
#     else:
#         print("AIS KEY: Not set")

# test_env()

# @login_required
# def trails_view(request):
#     return JsonResponse(history)

# @login_required
# def dashboard_map(request):
#     active_alerts = 0
#     return render(request, 'monitoring/dashboard.html', {'active_alerts': active_alerts})


# import requests
# from django.conf import settings

# from django.http import HttpResponse

# @login_required
# def proxy_map_image(request):
#     colab_url = getattr(settings, 'COLAB_API_URL')
#     try:
#         res = requests.get(f"{colab_url}/api/map-image", headers={'Bypass-Tunnel-Reminder': 'true'}, timeout=15)
#         return HttpResponse(res.content, content_type=res.headers.get('Content-Type', 'image/png'))
#     except Exception as e:
#         return HttpResponse(status=500)

# @login_required
# def trigger_mock_pipeline(request):
#     if request.method == 'POST':
#         colab_url = getattr(settings, 'COLAB_API_URL')
#         try:
#             res = requests.get(f"{colab_url}/api/scan", headers={'Bypass-Tunnel-Reminder': 'true'}, timeout=120)
#             print(res.status_code)
#             print(res.headers.get("Content-Type"))
#             print(res.text[:1000])
#             print("URL:", colab_url)
#             print("STATUS:", res.status_code)
#             print("BODY:", res.text[:300])
#             import json

#             if res.status_code != 200:
#                 return JsonResponse({
#                     "success": False,
#                     "message": f"Tunnel error: {res.status_code}",
#                     "raw": res.text[:300]
#                 })

#             try:
#                 data = res.json()
#             except Exception:
#                 return JsonResponse({
#                     "success": False,
#                     "message": "Invalid JSON from Colab tunnel",
#                     "raw": res.text[:300]
#                 })
#             if data.get("success"):
#                 ships = data.get("ships", [])
                
#                 # Inject explicit overlaps with the mocked AIS data
#                 ships.extend([
#                     {"lat": 43.1957483333333, "lon": 27.9097683333333, "confidence": 99.9},
#                     {"lat": 42.85, "lon": 28.2, "confidence": 98.5},
#                     {"lat": 43.35, "lon": 28.46, "confidence": 97.2}, # Overlaps Kaliakra + AIS
#                     {"lat": 42.60, "lon": 27.65, "confidence": 94.0}  # Overlaps Koketrays (SAR only, no AIS)
#                 ])

#                 return JsonResponse({
#                     "success": True, 
#                     "message": f"Scanned Sentinel-1 Data. Found {len(ships)} dark vessels!",
#                     "ships": ships,
#                     "image_url": "/monitoring/proxy-map-image/"
#                 })
#             else:
#                 return JsonResponse({"success": False, "message": data.get("message", "Unknown Colab error")})
#         except Exception as e:
#             return JsonResponse({"success": False, "message": str(e)})
            
#     return JsonResponse({"success": False, "message": "Invalid method"})