from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import IllegalReport


@login_required
def report_list(request):
    reports = IllegalReport.objects.all().order_by('-timestamp')
    return render(request, 'reports/report_list.html', {'reports': reports})


@login_required
def report_detail(request, pk):
    report = get_object_or_404(IllegalReport, pk=pk)

    if request.method == "POST":
        new_status = request.POST.get('status')
        if new_status in dict(IllegalReport.STATUS_CHOICES).keys():
            report.status = new_status
            report.save()
            return redirect('reports:report_list')

    return render(request, 'reports/report_detail.html', {'report': report})