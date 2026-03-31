from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required 
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.paginator import Paginator
from django.db.models import Q
import requests
import json
from .models import (
    PhongTro, TinTuc, HinhAnhPhongTro, HinhAnhTinTuc, 
    DonDatPhong, KhieuNai, DanhGia
)
from .forms import DangKyForm, UserUpdateForm

ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM0MmY1ZWQ3NjI0MzQ0NWM5NjVlZjA0NGQ2ZjE1NTIzIiwiaCI6Im11cm11cjY0In0=' 

BUSY_STATUS = [
    'cho_xac_nhan', 'cho_duyet', 'thanh_cong', 'confirmed', 
    'da_dat_coc', 'da_coc', 'success', 'pending'
]

def home(request):
    latest_rooms = PhongTro.objects.exclude(dondatphong__trang_thai__in=BUSY_STATUS).order_by('-created_at')[:3]
    
    try: 
        news = TinTuc.objects.order_by('-ngay_dang')[:3]
    except: 
        news = []
    
    return render(request, 'map_app/home.html', {'rooms': latest_rooms, 'news': news})

def map_view(request):
    rooms = PhongTro.objects.exclude(dondatphong__trang_thai__in=BUSY_STATUS)
    return render(request, 'map_app/map.html', {'rooms': rooms}) 

def room_detail(request, pk):
    phong = get_object_or_404(PhongTro, pk=pk)
    is_booked = DonDatPhong.objects.filter(phong=phong, trang_thai__in=BUSY_STATUS).exists()
    return render(request, 'map_app/detail.html', {'phong': phong, 'is_booked': is_booked})

def room_list(request):
    all_rooms = PhongTro.objects.exclude(dondatphong__trang_thai__in=['thanh_cong', 'da_dat_coc']).order_by('-id')
    search_query = request.GET.get('search', '')
    price_filter = request.GET.get('price', '')
    if search_query:
        all_rooms = all_rooms.filter(
            Q(ten__icontains=search_query) | Q(dia_chi__icontains=search_query)
        )
    if price_filter:
        if price_filter == 'under_2m':
            all_rooms = all_rooms.filter(gia_thue__lt=2000000)
        elif price_filter == '2m_5m':
            all_rooms = all_rooms.filter(gia_thue__range=(2000000, 5000000))
        elif price_filter == 'above_5m':
            all_rooms = all_rooms.filter(gia_thue__gt=5000000)
    paginator = Paginator(all_rooms, 6) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'map_app/room_list.html', {
        'rooms': page_obj,
        'search_query': search_query,
        'price_filter': price_filter
    })

def guide(request):
    return render(request, 'map_app/pages/guide.html')

def privacy(request):
    return render(request, 'map_app/pages/privacy.html')

@login_required
def complaint(request):
    if request.method == 'POST':
        tieu_de = request.POST.get('tieu_de')
        noi_dung = request.POST.get('noi_dung')
        KhieuNai.objects.create(
            nguoi_gui=request.user,
            tieu_de=tieu_de,
            noi_dung=noi_dung
        )
        messages.success(request, "Khiếu nại của bạn đã được gửi. Quản trị viên sẽ xử lý sớm nhất!")
        return redirect('complaint')
        
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
            
            phong_tros = PhongTro.objects.filter(location__within=poly).exclude(dondatphong__trang_thai__in=BUSY_STATUS)
            
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
    return redirect('admin_dashboard') if request.user.is_superuser else redirect('home')

@login_required
def saved_rooms(request):
    saved_list = request.user.favorite_rooms.all() 
    return render(request, 'map_app/saved_rooms.html', {'rooms': saved_list})

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

def news_list(request):
    return render(request, 'map_app/news_list.html', {'news': TinTuc.objects.order_by('-ngay_dang')})

def news_detail(request, pk):
    item = get_object_or_404(TinTuc, pk=pk)
    related = TinTuc.objects.exclude(pk=pk).order_by('-ngay_dang')[:5]
    return render(request, 'map_app/news_detail.html', {'news': item, 'related_news': related})

@login_required
def xac_nhan_dat_phong(request, room_id):
    phong = get_object_or_404(PhongTro, id=room_id)
    
    dang_ban = DonDatPhong.objects.filter(phong=phong, trang_thai__in=BUSY_STATUS).exists()
    
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

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser: 
        return redirect('home')
    return render(request, 'map_app/admin_custom/admin_base.html') 

@login_required
def custom_admin_users(request):
    if not request.user.is_superuser: 
        return redirect('home')
    danh_sach_user = User.objects.all().order_by('-date_joined')
    return render(request, 'map_app/admin_custom/user_list.html', {'danh_sach_user': danh_sach_user})

@login_required
def custom_admin_khoa_user(request, pk):
    if not request.user.is_superuser: return redirect('home')
    
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, "Lỗi: Bạn không thể tự khóa tài khoản của chính mình!")
    else:
        user_obj.is_active = not user_obj.is_active 
        user_obj.save()
        hanh_dong = "MỞ KHÓA" if user_obj.is_active else "KHÓA"
        messages.success(request, f"Đã {hanh_dong} tài khoản của {user_obj.username} thành công!")
        
    return redirect('custom_admin_users')

@login_required
def custom_admin_xoa_user(request, pk):
    if not request.user.is_superuser: return redirect('home')
    
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, "Lỗi: Bạn không thể tự xóa tài khoản của chính mình!")
    else:
        user_obj.delete()
        messages.success(request, f"Đã xóa vĩnh viễn người dùng {user_obj.username}!")
        
    return redirect('custom_admin_users')


@login_required
def custom_admin_edit_user(request, pk):
    if not request.user.is_superuser: 
        return redirect('home')

    user_obj = get_object_or_404(User, pk=pk)
    

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        user_obj.email = email
        
        if new_password and new_password.strip() != "":
            user_obj.set_password(new_password) 
            
        user_obj.save() 
        messages.success(request, f"Đã cập nhật tài khoản {user_obj.username} thành công!")
        return redirect('custom_admin_users')
        

    return render(request, 'map_app/admin_custom/user_edit.html', {'user_obj': user_obj})


@login_required
def custom_admin_phongtro(request):
    if not request.user.is_superuser: 
        return redirect('home')
    
    danh_sach_phong = PhongTro.objects.all().order_by('-created_at')
    
    return render(request, 'map_app/admin_custom/phongtro_list.html', {'danh_sach_phong': danh_sach_phong})

@login_required
def custom_admin_xoa_phongtro(request, pk):
    if not request.user.is_superuser: 
        return redirect('home')
    
    phong = get_object_or_404(PhongTro, pk=pk)
    ten_phong = phong.ten
    phong.delete() 
    
    messages.success(request, f"Đã xóa phòng trọ: {ten_phong} thành công!")
    return redirect('custom_admin_phongtro')

@login_required
def custom_admin_them_phongtro(request):
    if not request.user.is_superuser: return redirect('home')
    
    if request.method == 'POST':
        ten = request.POST.get('ten')
        gia_thue = request.POST.get('gia_thue')
        dia_chi = request.POST.get('dia_chi')
        hinh_anh = request.FILES.get('hinh_anh') 
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        
        location = Point(float(lng), float(lat), srid=4326) if lat and lng else None
        
        phong_moi = PhongTro.objects.create(
                    ten=ten, gia_thue=gia_thue, dia_chi=dia_chi,
                    hinh_anh=hinh_anh, location=location
                )
                
        danh_sach_anh_phu = request.FILES.getlist('hinh_anh_phu') 
        for file_anh in danh_sach_anh_phu:HinhAnhPhongTro.objects.create(phong=phong_moi, hinh_anh=file_anh)
        messages.success(request, "Thêm phòng trọ mới thành công!")
        return redirect('custom_admin_phongtro')
        
    return render(request, 'map_app/admin_custom/phongtro_form.html', {'action': 'Thêm Mới'})


@login_required
def custom_admin_sua_phongtro(request, pk):
    if not request.user.is_superuser: return redirect('home')
    phong = get_object_or_404(PhongTro, pk=pk)
    
    if request.method == 'POST':
        phong.ten = request.POST.get('ten')
        phong.gia_thue = request.POST.get('gia_thue')
        phong.dia_chi = request.POST.get('dia_chi')
        
        phong.mo_ta = request.POST.get('mo_ta') 

        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        
        if lat and lng:
            phong.location = Point(float(lng), float(lat), srid=4326)
            
        if 'hinh_anh' in request.FILES:
            phong.hinh_anh = request.FILES['hinh_anh']
            
        phong.save() 
        danh_sach_anh_phu = request.FILES.getlist('hinh_anh_phu')
        for file_anh in danh_sach_anh_phu:
            HinhAnhPhongTro.objects.create(phong=phong, hinh_anh=file_anh)
            
        messages.success(request, f"Đã cập nhật phòng {phong.ten}!")
        return redirect('custom_admin_phongtro')
        
    return render(request, 'map_app/admin_custom/phongtro_form.html', {'action': 'Chỉnh Sửa', 'phong': phong})

@login_required
def custom_admin_xoa_anh_daidien(request, pk):
    if not request.user.is_superuser: 
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            phong = get_object_or_404(PhongTro, pk=pk)
            if phong.hinh_anh:
                phong.hinh_anh.delete(save=False) 
                phong.hinh_anh = None 
                phong.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def custom_admin_xoa_anh_phongtro(request, anh_id):
    if not request.user.is_superuser: 
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            anh = get_object_or_404(HinhAnhPhongTro, pk=anh_id)
            anh.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def custom_admin_tintuc(request):
    if not request.user.is_superuser: return redirect('home')
    danh_sach_tin = TinTuc.objects.all().order_by('-ngay_dang')
    return render(request, 'map_app/admin_custom/tintuc_list.html', {'danh_sach_tin': danh_sach_tin})


@login_required
def custom_admin_them_tintuc(request):
    if not request.user.is_superuser: return redirect('home')
    
    if request.method == 'POST':
        tieu_de = request.POST.get('tieu_de')
        noi_dung = request.POST.get('noi_dung')
        hinh_anh = request.FILES.get('hinh_anh')
        tin_tuc_moi = TinTuc.objects.create(tieu_de=tieu_de, noi_dung=noi_dung, hinh_anh=hinh_anh)
    
        danh_sach_anh_phu = request.FILES.getlist('hinh_anh_phu')
        for file_anh in danh_sach_anh_phu:
            HinhAnhTinTuc.objects.create(tin_tuc=tin_tuc_moi, hinh_anh=file_anh)

        messages.success(request, "Thêm bài viết mới thành công!")
        return redirect('custom_admin_tintuc')
        
    return render(request, 'map_app/admin_custom/tintuc_form.html', {'action': 'Thêm Mới'})


@login_required
def custom_admin_sua_tintuc(request, pk):
    if not request.user.is_superuser: return redirect('home')
    tin_tuc = get_object_or_404(TinTuc, pk=pk)
    
    if request.method == 'POST':
        tin_tuc.tieu_de = request.POST.get('tieu_de')
        tin_tuc.noi_dung = request.POST.get('noi_dung')
        
        if 'hinh_anh' in request.FILES:
            tin_tuc.hinh_anh = request.FILES['hinh_anh']
            
        tin_tuc.save()
        danh_sach_anh_phu = request.FILES.getlist('hinh_anh_phu')
        for file_anh in danh_sach_anh_phu:
            HinhAnhTinTuc.objects.create(tin_tuc=tin_tuc, hinh_anh=file_anh)
            
        messages.success(request, f"Đã cập nhật bài viết: {tin_tuc.tieu_de}!")
        return redirect('custom_admin_tintuc')
        
    return render(request, 'map_app/admin_custom/tintuc_form.html', {'action': 'Chỉnh Sửa', 'tin_tuc': tin_tuc})


@login_required
def custom_admin_xoa_tintuc(request, pk):
    if not request.user.is_superuser: return redirect('home')
    tin_tuc = get_object_or_404(TinTuc, pk=pk)
    tin_tuc.delete()
    messages.success(request, "Đã xóa bài viết thành công!")
    return redirect('custom_admin_tintuc')

@login_required
def custom_admin_xoa_anh_daidien_tintuc(request, pk):
    if not request.user.is_superuser: 
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            tin_tuc = get_object_or_404(TinTuc, pk=pk)
            if tin_tuc.hinh_anh:
                tin_tuc.hinh_anh.delete(save=False)
                tin_tuc.hinh_anh = None
                tin_tuc.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def custom_admin_xoa_anh_phu_tintuc(request, anh_id):
    if not request.user.is_superuser: 
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            anh = get_object_or_404(HinhAnhTinTuc, pk=anh_id)
            anh.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def custom_admin_dondatphong(request):
    if not request.user.is_superuser: return redirect('home')
    danh_sach_don = DonDatPhong.objects.all().order_by('-ngay_tao')
    return render(request, 'map_app/admin_custom/dondatphong_list.html', {'danh_sach_don': danh_sach_don})

@login_required
def custom_admin_duyet_don(request, pk):
    if not request.user.is_superuser: return redirect('home')
    don = get_object_or_404(DonDatPhong, pk=pk)
    
    if request.method == 'POST':
        trang_thai_moi = request.POST.get('trang_thai')
        don.trang_thai = trang_thai_moi
        don.save()
        messages.success(request, f"Đã cập nhật trạng thái đơn của {don.nguoi_thue.username} thành công!")
        
    return redirect('custom_admin_dondatphong')

@login_required
def custom_admin_xoa_don(request, pk):
    if not request.user.is_superuser: return redirect('home')
    don = get_object_or_404(DonDatPhong, pk=pk)
    don.delete()
    messages.success(request, "Đã xóa đơn đặt phòng thành công!")
    return redirect('custom_admin_dondatphong')

@login_required
def gui_danh_gia(request, room_id):
    if request.method == 'POST':
        phong = get_object_or_404(PhongTro, id=room_id)
        DanhGia.objects.create(
            phong=phong,
            nguoi_danh_gia=request.user,
            so_sao=request.POST.get('so_sao'),
            noi_dung=request.POST.get('noi_dung')
        )
        messages.success(request, "Cảm ơn bạn đã gửi đánh giá!")
    return redirect('room_detail', pk=room_id)

@login_required
def gui_khieu_nai(request):
    if request.method == 'POST':
        KhieuNai.objects.create(
            nguoi_gui=request.user,
            tieu_de=request.POST.get('tieu_de'),
            noi_dung=request.POST.get('noi_dung')
        )
        messages.success(request, "Khiếu nại của bạn đã được gửi. Quản trị viên sẽ xử lý sớm nhất!")
        return redirect('gui_khieu_nai') 
    return render(request, 'map_app/complaint.html')


@login_required
def custom_admin_khieunai(request):
    if not request.user.is_superuser: return redirect('home')
    danh_sach = KhieuNai.objects.all().order_by('-ngay_tao')
    return render(request, 'map_app/admin_custom/khieunai_list.html', {'danh_sach': danh_sach})

@login_required
def custom_admin_cap_nhat_khieunai(request, pk):
    if not request.user.is_superuser: return redirect('home')
    khieu_nai = get_object_or_404(KhieuNai, pk=pk)
    if request.method == 'POST':
        khieu_nai.trang_thai = request.POST.get('trang_thai')
        khieu_nai.save()
        messages.success(request, "Đã cập nhật trạng thái khiếu nại!")
    return redirect('custom_admin_khieunai')

@login_required
def lich_su_khieu_nai(request):
    danh_sach = KhieuNai.objects.filter(nguoi_gui=request.user).order_by('-ngay_tao')
    return render(request, 'map_app/complaint_history.html', {'danh_sach': danh_sach})