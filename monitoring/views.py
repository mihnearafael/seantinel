from django.shortcuts import render, redirect
from django.contrib import messages
import folium
import random
from reports.models import ProtectedArea, IllegalReport

from django.http import JsonResponse
from .ais_monitoring import API_KEY, vessels, history

def vessels_view(request):
    return JsonResponse(list(vessels.values()), safe=False)

def test_env():
    print(f"AIS KEY: {API_KEY[:4]}...")

test_env()

def trails_view(request):
    return JsonResponse(history)

def dashboard_map(request):
    m = folium.Map(location=[44.8, 29.2], zoom_start=8, tiles='CartoDB dark_matter')

    areas = ProtectedArea.objects.all()
    for area in areas:
        folium.GeoJson(
            area.geometry_json,
            name=area.name,
            style_function=lambda x: {'fillColor': '#00ff00', 'color': '#00ff00', 'weight': 1, 'fillOpacity': 0.2}
        ).add_to(m)

    reports = IllegalReport.objects.exclude(status='FALSE_ALARM')
    for report in reports:
        color = "red" if report.status == "CONFIRMED" else "orange"
        folium.Marker(
            location=[report.latitude, report.longitude],
            popup=f"<b>{report.ship_name}</b><br>Score: {report.confidence_score}%<br>Status: {report.status}",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    context = {
        'map_html': m._repr_html_(),
        'active_alerts': reports.count(),
    }
    return render(request, 'monitoring/dashboard.html', context)


def trigger_mock_pipeline(request):
    if request.method == 'POST':
        lat = 44.5 + (random.random() * 0.8)
        lon = 29.0 + (random.random() * 1.5)

        IllegalReport.objects.create(
            latitude=lat,
            longitude=lon,
            confidence_score=random.randint(80, 99),
            status='UNCONFIRMED'
        )

        messages.success(request, f"Scanned Sentinel-1 Data. Found new dark vessel at {lat:.3f}, {lon:.3f}!")

    return redirect('monitoring:dashboard')