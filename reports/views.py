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
from django.http import JsonResponse, HttpResponse
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
                status = ship.get("status", "UNCONFIRMED")
                ship_name = ship.get("ship_name", "Dark Vessel (SAR)")
                zone_name = ship.get("zone_name", "")
                is_restricted = bool(zone_name)
                
                IllegalReport.objects.create(
                    scan_report=scan_report,
                    reported_by=request.user,
                    latitude=ship["lat"],
                    longitude=ship["lon"],
                    confidence_score=ship.get("confidence", 85),
                    status=status,
                    ship_name=ship_name,
                    in_restricted_area=is_restricted,
                    restricted_area_name=zone_name
                )
                created_count += 1
                
            return JsonResponse({"success": True, "message": f"Raport generat cu succes pentru {created_count} nave."})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
            
    return JsonResponse({"success": False, "message": "Cerere invalidă."})


def ro(text):
    """Strip Romanian diacritics so Helvetica renders them cleanly."""
    if not text:
        return ""
    replacements = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T',
        '\u015f': 's', '\u015e': 'S', '\u0163': 't', '\u0162': 'T',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


@login_required
def download_report_pdf(request, pk):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO

    report = get_object_or_404(ScanReport, pk=pk, reported_by=request.user)
    vessels = report.vessels.all()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"Raport Seantinel #{report.report_number}"
    )

    # Colour palette
    DARK_NAVY  = colors.HexColor('#0f172a')
    BLUE       = colors.HexColor('#0a84ff')
    RED        = colors.HexColor('#ff416c')
    AMBER      = colors.HexColor('#eab308')
    GREEN      = colors.HexColor('#0ba360')
    SLATE      = colors.HexColor('#64748b')
    LIGHT_GRAY = colors.HexColor('#f1f5f9')
    MID_GRAY   = colors.HexColor('#e2e8f0')

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', fontSize=22, fontName='Helvetica-Bold',
                                  textColor=DARK_NAVY, alignment=TA_CENTER, spaceAfter=4)
    sub_style   = ParagraphStyle('Sub',   fontSize=11, fontName='Helvetica',
                                  textColor=SLATE,     alignment=TA_CENTER, spaceAfter=2)
    section_style = ParagraphStyle('Section', fontSize=13, fontName='Helvetica-Bold',
                                    textColor=DARK_NAVY, spaceBefore=14, spaceAfter=6)
    body_style  = ParagraphStyle('Body',  fontSize=9,  fontName='Helvetica',
                                  textColor=DARK_NAVY, leading=14)
    small_style = ParagraphStyle('Small', fontSize=8,  fontName='Helvetica',
                                  textColor=SLATE, leading=12)

    STATUS_RO = {
        'UNCONFIRMED':  ro('Neconfirmat'),
        'INVESTIGATING': ro('In Investigatie'),
        'CONFIRMED':    ro('Ilegal Confirmat'),
        'FALSE_ALARM':  ro('Alarma Falsa'),
    }
    STATUS_COLOR = {
        'UNCONFIRMED':  AMBER,
        'INVESTIGATING': BLUE,
        'CONFIRMED':    RED,
        'FALSE_ALARM':  SLATE,
    }

    elems = []

    # ── Header ──────────────────────────────────────────────
    elems.append(Paragraph("SEANTINEL", title_style))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph(ro("Platforma Inteligenta de Monitorizare Geospatiala"), sub_style))
    elems.append(Spacer(1, 20))
    elems.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=20))

    # ── Report meta ──────────────────────────────────────────
    meta_data = [
        [ro("Raport Nr."), f"#{report.report_number}",
         ro("Data & Ora"),  report.timestamp.strftime("%d %B %Y, %H:%M UTC")],
        [ro("Utilizator"), ro(report.reported_by.username),
         ro("Institutie"),  ro(report.reported_by.institution_name or "-")],
        [ro("Rol"),        ro(report.reported_by.get_role_display() or "-"),
         ro("Total Nave"),  str(vessels.count())],
    ]
    meta_table = Table(meta_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_GRAY),
        ('BACKGROUND', (0,0), (0,-1), MID_GRAY),
        ('BACKGROUND', (2,0), (2,-1), MID_GRAY),
        ('FONTNAME',   (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME',   (0,0), (0,-1),  'Helvetica-Bold'),
        ('FONTNAME',   (2,0), (2,-1),  'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT_GRAY, MID_GRAY]),
        ('GRID',  (0,0), (-1,-1), 0.4, colors.HexColor('#cbd5e1')),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
    ]))
    elems.append(meta_table)
    elems.append(Spacer(1, 30))

    # ── Summary counts ───────────────────────────────────────
    confirmed    = vessels.filter(status='CONFIRMED').count()
    investigating = vessels.filter(status='INVESTIGATING').count()
    unconfirmed  = vessels.filter(status='UNCONFIRMED').count()
    false_alarm  = vessels.filter(status='FALSE_ALARM').count()

    elems.append(Paragraph(ro("Rezumat Detectii"), section_style))
    elems.append(Spacer(1, 10))
    summary_data = [
        [ro("Ilegal Confirmat"), ro("In Investigatie"), ro("Neconfirmat"), ro("Alarma Falsa")],
        [str(confirmed), str(investigating), str(unconfirmed), str(false_alarm)],
    ]
    summary_table = Table(summary_data, colWidths=[4.25*cm]*4)
    summary_table.setStyle(TableStyle([
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME',   (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTNAME',   (0,1), (-1,1),  'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,0),  9),
        ('FONTSIZE',   (0,1), (-1,1),  20),
        ('TEXTCOLOR',  (0,0), (0,-1),  RED),
        ('TEXTCOLOR',  (1,0), (1,-1),  BLUE),
        ('TEXTCOLOR',  (2,0), (2,-1),  AMBER),
        ('TEXTCOLOR',  (3,0), (3,-1),  SLATE),
        ('BACKGROUND', (0,0), (0,-1),  colors.HexColor('#fff1f2')),
        ('BACKGROUND', (1,0), (1,-1),  colors.HexColor('#eff6ff')),
        ('BACKGROUND', (2,0), (2,-1),  colors.HexColor('#fefce8')),
        ('BACKGROUND', (3,0), (3,-1),  colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#cbd5e1')),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    elems.append(summary_table)
    elems.append(Spacer(1, 30))

    # ── Vessel detail table ──────────────────────────────────
    elems.append(Paragraph(ro("Detalii Nave Detectate"), section_style))
    elems.append(Spacer(1, 10))
    elems.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY, spaceAfter=8))

    headers = ["#", ro("Nava"), ro("Coordonate"), ro("Zona Restrictionata"), ro("Incredere AI"), "Status"]
    rows = [headers]
    for i, v in enumerate(vessels, 1):
        restricted = ro(v.restricted_area_name) if v.in_restricted_area else "-"
        rows.append([
            str(i),
            Paragraph(ro(v.ship_name), body_style),
            Paragraph(f"{v.latitude:.4f},\n{v.longitude:.4f}", small_style),
            Paragraph(restricted, body_style),
            f"{v.confidence_score}%",
            Paragraph(STATUS_RO.get(v.status, v.status), body_style),
        ])

    vessel_table = Table(rows, colWidths=[0.8*cm, 3.5*cm, 2.8*cm, 4*cm, 2*cm, 3.9*cm])
    ts = TableStyle([
        # Header row
        ('BACKGROUND',  (0,0), (-1,0), DARK_NAVY),
        ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,0), 8),
        ('ALIGN',       (0,0), (-1,0), 'CENTER'),
        ('TOPPADDING',  (0,0), (-1,0), 8),
        ('BOTTOMPADDING',(0,0),(-1,0), 8),
        # Body rows
        ('FONTNAME',    (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',    (0,1), (-1,-1), 8),
        ('ALIGN',       (0,1), (-1,-1), 'CENTER'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, LIGHT_GRAY]),
        ('GRID',        (0,0), (-1,-1), 0.4, colors.HexColor('#cbd5e1')),
        ('TOPPADDING',  (0,1), (-1,-1), 6),
        ('BOTTOMPADDING',(0,1),(-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ])
    # Colour-code status cells
    for i, v in enumerate(vessels, 1):
        c = STATUS_COLOR.get(v.status, SLATE)
        ts.add('TEXTCOLOR', (5, i), (5, i), c)
        ts.add('FONTNAME',  (5, i), (5, i), 'Helvetica-Bold')

    vessel_table.setStyle(ts)
    elems.append(vessel_table)
    elems.append(Spacer(1, 30))

    # ── Footer ───────────────────────────────────────────────
    elems.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY, spaceAfter=6))
    elems.append(Paragraph(
        ro(f"Document generat automat de platforma Seantinel - ") +
        f"{report.timestamp.strftime('%d.%m.%Y')} - " +
        ro(f"Utilizator: {report.reported_by.username}"),
        ParagraphStyle('Footer', fontSize=7, textColor=SLATE, alignment=TA_CENTER)
    ))

    doc.build(elems)
    buffer.seek(0)
    filename = f"seantinel_raport_{report.report_number}_{report.timestamp.strftime('%Y%m%d')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response