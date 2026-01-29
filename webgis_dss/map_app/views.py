from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.gis.geos import GEOSGeometry
from .models import PhongTro
import requests
import json

# --- CẤU HÌNH ---
# Dán cái Key bắt đầu bằng "cy..." của bạn vào giữa 2 dấu nháy bên dưới:
ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM0MmY1ZWQ3NjI0MzQ0NWM5NjVlZjA0NGQ2ZjE1NTIzIiwiaCI6Im11cm11cjY0In0='

def index(request):
    """Hàm này để hiển thị trang chủ (Giao diện bản đồ)"""
    return render(request, 'map_app/index.html')

def search_api(request):
    """Hàm này nhận yêu cầu từ web, tính toán và trả về kết quả"""
    try:
        # 1. Lấy dữ liệu người dùng gửi lên (Tọa độ và thời gian)
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        time_min = int(request.GET.get('time'))

        # 2. Gọi OpenRouteService để tính vùng đi lại (Isochrone)
        headers = {
            'Authorization': ORS_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Cấu hình gửi đi
        body = {
            "locations": [[lng, lat]], # Lưu ý: ORS dùng [Kinh độ, Vĩ độ]
            "range": [time_min * 60],  # Đổi phút sang giây
            "range_type": "time",
            "attributes": ["area"]
        }
        
        # Gửi request
        response = requests.post(
            "https://api.openrouteservice.org/v2/isochrones/driving-car",
            json=body,
            headers=headers
        )
        
        # Kiểm tra nếu lỗi
        if response.status_code != 200:
            return JsonResponse({'error': 'Lỗi kết nối bản đồ. Kiểm tra lại API Key!'}, status=400)

        data = response.json()
        
        # 3. Xử lý kết quả trả về
        # Lấy hình đa giác (Polygon) từ dữ liệu JSON
        geometry_json = json.dumps(data['features'][0]['geometry'])
        polygon = GEOSGeometry(geometry_json)

        # 4. Truy vấn Database (Tìm phòng trọ nằm TRONG vùng này)
        # __within là câu lệnh thần thánh của PostGIS
        phong_tros = PhongTro.objects.filter(location__within=polygon)

        # 5. Đóng gói kết quả gửi về cho Web
        results = []
        for p in phong_tros:
            results.append({
                'id': p.id,
                'ten': p.ten,
                'gia': p.gia_thue,
                'dia_chi': p.dia_chi,
                'lat': p.location.y,
                'lng': p.location.x
            })

        return JsonResponse({
            'success': True,
            'polygon': data,   # Vùng xanh để vẽ
            'rooms': results,  # Danh sách phòng để hiện
            'count': len(results)
        })

    except Exception as e:
        print(f"Lỗi Server: {e}")
        return JsonResponse({'error': str(e)}, status=500)