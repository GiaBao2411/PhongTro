from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required 
from django.contrib import messages
import requests
import json
from .forms import DangKyForm, UserUpdateForm
from .models import PhongTro, TinTuc, DonDatPhong

ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM0MmY1ZWQ3NjI0MzQ0NWM5NjVlZjA0NGQ2ZjE1NTIzIiwiaCI6Im11cm11cjY0In0=' 

def home(request):
    trang_thai_ban = ['cho_xac_nhan', 'cho_duyet', 'thanh_cong']
    
    latest_rooms = PhongTro.objects.exclude(dondatphong__trang_thai__in=trang_thai_ban)[:3]
    
    try: 
        news = TinTuc.objects.order_by('-ngay_dang')[:3]
    except: 
        news = []
    
    return render(request, 'map_app/home.html', {'rooms': latest_rooms, 'news': news})

def map_view(request):
    return render(request, 'map_app/map.html') 

def room_detail(request, pk):
    phong = get_object_or_404(PhongTro, pk=pk)
    return render(request, 'map_app/detail.html', {'phong': phong})

def room_list(request):
    trang_thai_ban = ['cho_xac_nhan', 'cho_duyet', 'thanh_cong']
    all_rooms = PhongTro.objects.exclude(dondatphong__trang_thai__in=trang_thai_ban).order_by('-created_at')
    return render(request, 'map_app/room_list.html', {'rooms': all_rooms})

def guide(request):
    return render(request, 'map_app/pages/guide.html')

def privacy(request):
    return render(request, 'map_app/pages/privacy.html')

def complaint(request):
    return render(request, 'map_app/pages/complaint.html')

def faq(request):
    return render(request, 'map_app/pages/faq.html')

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
            
            trang_thai_ban = ['cho_xac_nhan', 'cho_duyet', 'thanh_cong']
            phong_tros = PhongTro.objects.filter(location__within=poly).exclude(dondatphong__trang_thai__in=trang_thai_ban)
            
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

@login_required
def xac_nhan_dat_phong(request, room_id):
    phong = get_object_or_404(PhongTro, id=room_id)
    dang_ban = DonDatPhong.objects.filter(phong=phong).exclude(trang_thai='huy').exists()
    if dang_ban:
        messages.warning(request, "⚠️ Chậm chân rồi! Phòng này vừa có người khác đặt giữ chỗ.")
        return redirect('home')
    if request.method == 'POST':
        ngay_don = request.POST.get('ngay_don_vao')
        loi_nhan = request.POST.get('loi_nhan')  
        don_moi = DonDatPhong.objects.create(
            nguoi_thue=request.user,
            phong=phong,
            ngay_don_vao=ngay_don,
            tien_coc=phong.gia_thue,
            ghi_chu=loi_nhan,
            trang_thai='cho_xac_nhan'
        )
        return redirect('thanh_toan', don_id=don_moi.id) 
    return render(request, 'map_app/booking.html', {'phong': phong})

@login_required
def thanh_toan(request, don_id):
    don = get_object_or_404(DonDatPhong, id=don_id, nguoi_thue=request.user)
    if request.method == 'POST':
        don.trang_thai = 'cho_duyet' 
        don.save()
        messages.success(request, "Đã gửi xác nhận! Admin sẽ liên hệ bạn sớm.")
        return redirect('home')
    noi_dung_ck = f"DAT COC PHONG {don.phong.id}"
    qr_url = f"https://img.vietqr.io/image/Sacombank-060308333003-compact.jpg?amount={int(don.tien_coc)}&addInfo={noi_dung_ck}&accountName=CHU_TRO"
    return render(request, 'map_app/payment.html', {'don': don, 'qr_url': qr_url})

@login_required
def booking_history(request):
    history = DonDatPhong.objects.filter(nguoi_thue=request.user).order_by('-ngay_tao')
    
    return render(request, 'map_app/booking_history.html', {'history': history})