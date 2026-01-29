from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.gis.geos import GEOSGeometry
from .models import PhongTro
import requests
import json
import traceback

# --- CẤU HÌNH API ---
# Nhớ dán Key cy... của bạn vào đây nhé
ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM0MmY1ZWQ3NjI0MzQ0NWM5NjVlZjA0NGQ2ZjE1NTIzIiwiaCI6Im11cm11cjY0In0=' 

# 1. HÀM TRANG CHỦ (MỚI) - Để hiện giao diện giới thiệu đẹp
def home(request):
    # Lấy 6 phòng trọ mới nhất để hiện ra trang chủ
    latest_rooms = PhongTro.objects.order_by('-created_at')[:6]
    return render(request, 'map_app/home.html', {'rooms': latest_rooms})

# 2. HÀM BẢN ĐỒ (ĐỔI TÊN TỪ INDEX CŨ) - Để hiện chức năng GIS
def map_view(request):
    return render(request, 'map_app/map.html') 

# 3. TRANG CHI TIẾT
def room_detail(request, pk):
    phong = get_object_or_404(PhongTro, pk=pk)
    return render(request, 'map_app/detail.html', {'phong': phong})

# 4. API TÌM KIẾM (Tool 1 & 2)
def search_api(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        time_min = int(request.GET.get('time'))
        
        print(f"👉 Đang tìm: Lat={lat}, Lng={lng}, Time={time_min}")

        headers = {
            'Authorization': ORS_API_KEY.strip(),
            'Content-Type': 'application/json'
        }
        body = {
            "locations": [[lng, lat]], 
            "range": [time_min * 60], 
            "range_type": "time", 
            "attributes": ["area"]
        }
        
        response = requests.post("https://api.openrouteservice.org/v2/isochrones/driving-car", json=body, headers=headers)
        
        if response.status_code != 200:
            return JsonResponse({'error': f'Lỗi API: {response.text}'}, status=400)

        data = response.json()
        geometry_json = json.dumps(data['features'][0]['geometry'])
        polygon = GEOSGeometry(geometry_json)

        phong_tros = PhongTro.objects.filter(location__within=polygon)
        
        results = []
        for p in phong_tros:
            img_url = p.hinh_anh.url if p.hinh_anh else ""
            results.append({
                'id': p.id, 'ten': p.ten, 'gia': p.gia_thue, 
                'dia_chi': p.dia_chi, 'lat': p.location.y, 'lng': p.location.x,
                'img': img_url
            })

        return JsonResponse({'success': True, 'polygon': data, 'rooms': results, 'count': len(results)})

    except Exception as e:
        print("❌ LỖI SERVER:")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

# 5. API DẪN ĐƯỜNG (Tool 3)
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