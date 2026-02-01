from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.functions import Distance
from .models import PhongTro
from .forms import DangKyForm
from django.contrib.auth import login
import requests

ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM0MmY1ZWQ3NjI0MzQ0NWM5NjVlZjA0NGQ2ZjE1NTIzIiwiaCI6Im11cm11cjY0In0='

def home(request):
    latest_rooms = PhongTro.objects.order_by('-created_at')[:6]
    return render(request, 'map_app/home.html', {'rooms': latest_rooms})

def map_view(request):
    return render(request, 'map_app/map.html')

def room_detail(request, pk):
    phong = get_object_or_404(PhongTro, pk=pk)
    return render(request, 'map_app/detail.html', {'phong': phong})

def filter_rooms_api(request):
    try:
        lat = float(request.GET.get('lat', 0))
        lng = float(request.GET.get('lng', 0))
        radius_m = float(request.GET.get('radius', 2000))
        
        user_point = GEOSGeometry(f'POINT({lng} {lat})', srid=4326)

        # Lọc phòng trọ trong bán kính và tính khoảng cách chim bay
        rooms = PhongTro.objects.filter(
            location__distance_lte=(user_point, radius_m)
        ).annotate(distance=Distance('location', user_point)).order_by('distance')

        results = []
        for p in rooms:
            dist_m = p.distance.m if hasattr(p, 'distance') else 0
            results.append({
                'id': p.id,
                'ten': p.ten,
                'gia': p.gia_thue,
                'lat': p.location.y,
                'lng': p.location.x,
                'distance_km': round(dist_m / 1000, 2)
            })
        return JsonResponse({'rooms': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def route_api(request):
    try:
        start_lat = request.GET.get('start_lat')
        start_lng = request.GET.get('start_lng')
        end_lat = request.GET.get('end_lat')
        end_lng = request.GET.get('end_lng')
        
        url = f"https://api.openrouteservice.org/v2/directions/driving-car?start={start_lng},{start_lat}&end={end_lng},{end_lat}"
        headers = {'Authorization': ORS_API_KEY.strip()}
        response = requests.get(url, headers=headers)
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def register(request):
    if request.method == "POST":
        form = DangKyForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = DangKyForm()
    return render(request, 'map_app/register.html', {'form': form})

def login_success(request):
    return redirect('/admin/') if request.user.is_superuser else redirect('home')