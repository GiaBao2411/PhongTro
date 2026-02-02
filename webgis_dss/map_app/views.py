from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required 
from .forms import DangKyForm, UserUpdateForm  
from django.contrib import messages
from .models import PhongTro, TinTuc
from .forms import DangKyForm
import requests
import json

# API Key OpenRouteService
ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM0MmY1ZWQ3NjI0MzQ0NWM5NjVlZjA0NGQ2ZjE1NTIzIiwiaCI6Im11cm11cjY0In0=' 

# ==========================
# 1. CÁC VIEW HIỂN THỊ HTML
# ==========================

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

# Danh sách tất cả phòng (Thêm vào cho đủ bộ)
def room_list(request):
    all_rooms = PhongTro.objects.all().order_by('-created_at')
    return render(request, 'map_app/room_list.html', {'rooms': all_rooms})

# ==========================
# 2. CÁC API XỬ LÝ BẢN ĐỒ
# ==========================

# API Tìm kiếm thông minh (Isochrone)
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
        
        if response.status_code != 200:
            return JsonResponse({'error': 'Lỗi API ORS'}, status=400)

        data = response.json()
        if 'features' in data:
            poly = GEOSGeometry(json.dumps(data['features'][0]['geometry']))
            phong_tros = PhongTro.objects.filter(location__within=poly)
            results = []
            for p in phong_tros:
                img_url = p.hinh_anh.url if p.hinh_anh else ""
                results.append({
                    'id': p.id, 'ten': p.ten, 'gia': p.gia_thue, 
                    'dia_chi': p.dia_chi, 'lat': p.location.y, 'lng': p.location.x, 'img': img_url
                })
            return JsonResponse({'success': True, 'polygon': data, 'rooms': results})
        return JsonResponse({'error': 'Không tìm thấy dữ liệu vùng'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# API Dẫn đường
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

# API Thả tim
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

# ==========================
# 3. USER & NEWS
# ==========================

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
    saved_list = request.user.favorite_rooms.all() 
    return render(request, 'map_app/saved_rooms.html', {'rooms': saved_list})

def news_list(request):
    return render(request, 'map_app/news_list.html', {'news': TinTuc.objects.order_by('-ngay_dang')})

def news_detail(request, pk):
    item = get_object_or_404(TinTuc, pk=pk)
    related = TinTuc.objects.exclude(pk=pk).order_by('-ngay_dang')[:5]
    return render(request, 'map_app/news_detail.html', {'news': item, 'related_news': related})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, 'Cập nhật thông tin thành công!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)

    context = {
        'u_form': u_form
    }
    return render(request, 'map_app/profile.html', context)