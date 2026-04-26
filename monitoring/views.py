from django.shortcuts import render, redirect
from django.contrib import messages
import folium
import random
from reports.models import ProtectedArea, IllegalReport

from django.http import JsonResponse
from .ais_monitoring import API_KEY, vessels, history

from django.contrib.auth.decorators import login_required

@login_required
def vessels_view(request):
    return JsonResponse(list(vessels.values()), safe=False)

def test_env():
    if API_KEY:
        print(f"AIS KEY: {API_KEY[:4]}...")
    else:
        print("AIS KEY: Not set")

test_env()

@login_required
def trails_view(request):
    return JsonResponse(history)

@login_required
def dashboard_map(request):
    active_alerts = 0
    return render(request, 'monitoring/dashboard.html', {'active_alerts': active_alerts})


import requests
from django.conf import settings

from django.http import HttpResponse

@login_required
def proxy_map_image(request):
    colab_url = getattr(settings, 'COLAB_API_URL', 'https://chubby-sheep-grin.loca.lt')
    try:
        res = requests.get(f"{colab_url}/api/map-image", headers={'Bypass-Tunnel-Reminder': 'true'}, timeout=15)
        return HttpResponse(res.content, content_type=res.headers.get('Content-Type', 'image/png'))
    except Exception as e:
        return HttpResponse(status=500)

@login_required
def trigger_mock_pipeline(request):
    if request.method == 'POST':
        colab_url = getattr(settings, 'COLAB_API_URL', 'https://chubby-sheep-grin.loca.lt')
        try:
            res = requests.get(f"{colab_url}/api/scan", headers={'Bypass-Tunnel-Reminder': 'true'}, timeout=120)
            data = res.json()
            if data.get("success"):
                ships = data.get("ships", [])
                
                # Inject explicit overlaps with the mocked AIS data
                ships.extend([
                    {"lat": 43.1957483333333, "lon": 27.9097683333333, "confidence": 99.9},
                    {"lat": 42.85, "lon": 28.2, "confidence": 98.5},
                    {"lat": 43.35, "lon": 28.46, "confidence": 97.2}, # Overlaps Kaliakra + AIS
                    {"lat": 42.60, "lon": 27.65, "confidence": 94.0}  # Overlaps Koketrays (SAR only, no AIS)
                ])

                return JsonResponse({
                    "success": True, 
                    "message": f"Scanned Sentinel-1 Data. Found {len(ships)} dark vessels!",
                    "ships": ships,
                    "image_url": "/monitoring/proxy-map-image/"
                })
            else:
                return JsonResponse({"success": False, "message": data.get("message", "Unknown Colab error")})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
            
    return JsonResponse({"success": False, "message": "Invalid method"})