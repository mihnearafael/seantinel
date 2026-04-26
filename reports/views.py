from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import IllegalReport, ScanReport

@login_required
def report_list(request):
    reports = ScanReport.objects.filter(reported_by=request.user).order_by('-timestamp')
    return render(request, 'reports/report_list.html', {'reports': reports})


@login_required
def report_detail(request, pk):
    report = get_object_or_404(ScanReport, pk=pk, reported_by=request.user)

    if request.method == "POST":
        vessel_id = request.POST.get('vessel_id')
        new_status = request.POST.get('status')
        if vessel_id and new_status in dict(IllegalReport.STATUS_CHOICES).keys():
            vessel = get_object_or_404(IllegalReport, pk=vessel_id, scan_report=report)
            vessel.status = new_status
            vessel.save()
            return redirect('reports:report_detail', pk=pk)

    return render(request, 'reports/report_detail.html', {'report': report})

import json
from django.http import JsonResponse

import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

RESTRICTED_ZONES = [
    {"name": "Kaliakra Reserve", "lat": 43.361389, "lon": 28.465000, "radius_km": 0.5},
    {"name": "Veleka River Mouth", "lat": 42.066944, "lon": 27.971944, "radius_km": 0.5},
    {"name": "Ropotamo River Mouth", "lat": 42.327778, "lon": 27.756389, "radius_km": 0.5},
    {"name": "Varna Port Restriction", "lat": 43.193333, "lon": 27.909722, "radius_km": 2.0},
    {"name": "Burgas Port Restriction", "lat": 42.489444, "lon": 27.487500, "radius_km": 2.0},
    {"name": "Koketrays Sandbank", "lat": 42.583333, "lon": 27.666667, "radius_km": 5.0},
]

def check_restricted_zones(lat, lon):
    for zone in RESTRICTED_ZONES:
        if haversine(lat, lon, zone["lat"], zone["lon"]) <= zone["radius_km"]:
            return True, zone["name"]
    return False, None

@login_required
def generate_report(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            ships = data.get("ships", [])
            
            last_report = ScanReport.objects.filter(reported_by=request.user).order_by('-report_number').first()
            next_number = (last_report.report_number + 1) if last_report else 1
            
            scan_report = ScanReport.objects.create(
                reported_by=request.user,
                report_number=next_number
            )
            created_count = 0
            for ship in ships:
                is_restricted, zone_name = check_restricted_zones(ship["lat"], ship["lon"])
                IllegalReport.objects.create(
                    scan_report=scan_report,
                    reported_by=request.user,
                    latitude=ship["lat"],
                    longitude=ship["lon"],
                    confidence_score=ship.get("confidence", 85),
                    status='UNCONFIRMED',
                    ship_name="Dark Vessel (SAR)",
                    in_restricted_area=is_restricted,
                    restricted_area_name=zone_name
                )
                created_count += 1
                
            return JsonResponse({"success": True, "message": f"Successfully generated report for {created_count} vessels."})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
            
    return JsonResponse({"success": False, "message": "Invalid request."})