from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import PhongTro, TinTuc
from .forms import DangKyForm
import requests
import json

# API Key ORS
ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM0MmY1ZWQ3NjI0MzQ0NWM5NjVlZjA0NGQ2ZjE1NTIzIiwiaCI6Im11cm11cjY0In0=' 

# --- VIEWS CƠ BẢN ---
def home(request):
    latest_rooms = PhongTro.objects.order_by('-created_at')[:6]
    try: news = TinTuc.objects.order_by('-ngay_dang')[:3]
    except: news = []
    return render(request, 'map_app/home.html', {'rooms': latest_rooms, 'news': news})

def map_view(request):
    return render(request, 'map_app/map.html') 

def room_detail(request, pk):
    phong = get_object_or_404(PhongTro, pk=pk)
    return render(request, 'map_app/detail.html', {'phong': phong})

# --- API GIS (TÌM KIẾM) ---
def search_api(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        mode = request.GET.get('mode', 'time')
        input_val = float(request.GET.get('value'))
        vehicle = request.GET.get('vehicle', 'moto') 
        is_rush_hour = request.GET.get('rush_hour') == 'true'

        speed_map = {'moto': 35, 'car': 30, 'walk': 5}
        van_toc = speed_map.get(vehicle, 30)
        if is_rush_hour and vehicle != 'walk': van_toc *= 0.6 

        if mode == 'time':
            range_val = (input_val / 60) * van_toc * 1000 
            range_type = 'distance' 
        else:
            range_val = input_val * 1000 
            range_type = 'distance'

        headers = {'Authorization': ORS_API_KEY.strip(), 'Content-Type': 'application/json'}
        body = {"locations": [[lng, lat]], "range": [range_val], "range_type": range_type, "attributes": ["area"]}
        
        response = requests.post("https://api.openrouteservice.org/v2/isochrones/driving-car", json=body, headers=headers)
        data = response.json()
        
        if 'features' in data:
            poly = GEOSGeometry(json.dumps(data['features'][0]['geometry']))
            phong_tros = PhongTro.objects.filter(location__within=poly)
            results = [{'id': p.id, 'ten': p.ten, 'gia': p.gia_thue, 'dia_chi': p.dia_chi, 'lat': p.location.y, 'lng': p.location.x, 'img': p.hinh_anh.url if p.hinh_anh else ""} for p in phong_tros]
            return JsonResponse({'success': True, 'polygon': data, 'rooms': results})
        return JsonResponse({'error': 'Lỗi API'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --- API DẪN ĐƯỜNG ---
def route_api(request):
    try:
        start_lat = request.GET.get('start_lat')
        start_lng = request.GET.get('start_lng')
        end_lat = request.GET.get('end_lat')
        end_lng = request.GET.get('end_lng')
        vehicle = request.GET.get('vehicle', 'moto')
        is_rush_hour = request.GET.get('rush_hour') == 'true'

        profile = 'foot-walking' if vehicle == 'walk' else 'driving-car'
        url = f"https://api.openrouteservice.org/v2/directions/{profile}?start={start_lng},{start_lat}&end={end_lng},{end_lat}"
        
        resp = requests.get(url, headers={'Authorization': ORS_API_KEY.strip()}).json()
        if 'features' in resp:
            dist_km = resp['features'][0]['properties']['summary']['distance'] / 1000
            speed = {'moto': 35, 'car': 30, 'walk': 5}.get(vehicle, 30)
            if is_rush_hour and vehicle != 'walk': speed *= 0.6
            resp['features'][0]['properties']['summary']['duration'] = (dist_km / speed) * 3600
        return JsonResponse(resp)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --- API THẢ TIM ---
@login_required
def toggle_favorite(request, pk):
    try:
        phong = get_object_or_404(PhongTro, pk=pk)
        if request.user in phong.favorites.all():
            phong.favorites.remove(request.user)
            liked = False
        else:
            phong.favorites.add(request.user)
            liked = True
        return JsonResponse({'success': True, 'liked': liked})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# --- AUTH & USER ---
def register(request):
    if request.method == "POST":
        form = DangKyForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else: form = DangKyForm()
    return render(request, 'map_app/register.html', {'form': form})

def login_success(request):
    return redirect('/admin/') if request.user.is_superuser else redirect('home')

@login_required
def profile(request):
    return render(request, 'map_app/profile.html')

@login_required
def saved_rooms(request):
    # Lấy danh sách thật
    saved_list = request.user.favorite_rooms.all() 
    return render(request, 'map_app/saved_rooms.html', {'rooms': saved_list})

# --- NEWS ---
def news_list(request):
    return render(request, 'map_app/news_list.html', {'news': TinTuc.objects.order_by('-ngay_dang')})

def news_detail(request, pk):
    item = get_object_or_404(TinTuc, pk=pk)
    related = TinTuc.objects.exclude(pk=pk).order_by('-ngay_dang')[:5]
    return render(request, 'map_app/news_detail.html', {'news': item, 'related_news': related})