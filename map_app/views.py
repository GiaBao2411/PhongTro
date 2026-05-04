from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required 
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from functools import wraps
import requests
import json
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.urls import reverse
from .models import NhaTro, PhongTro, HinhAnhNhaTro, TinTuc, HinhAnhTinTuc, DonDatPhong, DanhGia, KhieuNai, TrangGioiThieu, HoSoChuTro
from .forms import DangKyForm, UserUpdateForm

ORS_API_KEY = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjM0MmY1ZWQ3NjI0MzQ0NWM5NjVlZjA0NGQ2ZjE1NTIzIiwiaCI6Im11cm11cjY0In0=' 
signer = TimestampSigner()

def admin_only(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            raise PermissionDenied("Bạn không có quyền truy cập khu vực Quản trị!")
        return view_func(request, *args, **kwargs)
    return wrapper_func

def chu_tro_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if hasattr(request.user, 'ho_so_chu_tro'):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Bạn không có quyền truy cập khu vực này!")
    return wrapper

def is_chu_tro(user):
    return user.is_superuser or hasattr(user, 'ho_so_chu_tro')

def home(request):
    danh_sach_nha = NhaTro.objects.all().order_by('-created_at')[:3]
    for nha in danh_sach_nha:
        nha.so_phong_trong = nha.danh_sach_phong.filter(trang_thai='trong').count()
        nha.tong_so_phong = nha.danh_sach_phong.count()
        phong_re_nhat = nha.danh_sach_phong.order_by('gia_thue').first()
        nha.gia_thap_nhat = phong_re_nhat.gia_thue if phong_re_nhat else 0

    try: 
        news = TinTuc.objects.order_by('-ngay_dang')[:3]
    except: 
        news = []
    return render(request, 'map_app/home.html', {'rooms': danh_sach_nha, 'news': news})

def map_view(request):
    nha_tros = NhaTro.objects.all()
    rooms = []
    for nha in nha_tros:
        if nha.danh_sach_phong.filter(trang_thai='trong').exists():
            nha.ten = nha.ten_nha 
            phong_re = nha.danh_sach_phong.order_by('gia_thue').first()
            nha.gia_thue = phong_re.gia_thue if phong_re else 0
            rooms.append(nha)
    return render(request, 'map_app/map.html', {'rooms': rooms})

def room_list(request):
    search_query = request.GET.get('search', '')
    price_filter = request.GET.get('price', '')
    all_nha = NhaTro.objects.all().order_by('-id')
    
    if search_query:
        all_nha = all_nha.filter(Q(ten_nha__icontains=search_query) | Q(dia_chi__icontains=search_query))
        
    nha_hien_thi = []
    for nha in all_nha:
        nha.so_phong_trong = nha.danh_sach_phong.filter(trang_thai='trong').count()
        nha.tong_so_phong = nha.danh_sach_phong.count()
        phong_re = nha.danh_sach_phong.order_by('gia_thue').first()
        nha.gia_thap_nhat = phong_re.gia_thue if phong_re else 0
        
        if price_filter == 'under_2m' and nha.gia_thap_nhat >= 2000000: continue
        if price_filter == '2m_5m' and (nha.gia_thap_nhat < 2000000 or nha.gia_thap_nhat > 5000000): continue
        if price_filter == 'above_5m' and nha.gia_thap_nhat <= 5000000: continue
        
        nha.ten = nha.ten_nha 
        nha.gia_thue = nha.gia_thap_nhat
        nha_hien_thi.append(nha)

    paginator = Paginator(nha_hien_thi, 6) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'map_app/room_list.html', {
        'rooms': page_obj,
        'search_query': search_query,
        'price_filter': price_filter
    })

def room_detail(request, pk):
    nha = get_object_or_404(NhaTro, pk=pk)
    phong_trong = nha.danh_sach_phong.filter(trang_thai='trong')
    nha.ten = nha.ten_nha
    phong_re = nha.danh_sach_phong.order_by('gia_thue').first()
    nha.gia_thue = phong_re.gia_thue if phong_re else 0
 
    da_danh_gia = False
    if request.user.is_authenticated:
        da_danh_gia = DanhGia.objects.filter(nha_tro=nha, nguoi_danh_gia=request.user).exists()
 
    return render(request, 'map_app/detail.html', {
        'phong': nha,
        'phong_trong': phong_trong,
        'da_danh_gia': da_danh_gia,
    })

@login_required
def xac_nhan_dat_phong(request, room_id):
    phong_duoc_chon = get_object_or_404(PhongTro, id=room_id)
    if phong_duoc_chon.trang_thai != 'trong':
        messages.warning(request, "⚠️ Chậm chân rồi! Phòng này vừa có người khác đặt giữ chỗ.")
        return redirect('room_detail', pk=phong_duoc_chon.nha_tro.id)
        
    if request.method == 'POST':
        ngay_don = request.POST.get('ngay_don_vao')
        loi_nhan = request.POST.get('loi_nhan')  
        don_moi = DonDatPhong.objects.create(
            nguoi_thue=request.user,
            phong=phong_duoc_chon,
            ngay_don_vao=ngay_don,
            tien_coc=phong_duoc_chon.gia_thue,
            ghi_chu=loi_nhan,
            trang_thai='cho_xac_nhan'
        )
        phong_duoc_chon.trang_thai = 'da_dat'
        phong_duoc_chon.save()
        return redirect('thanh_toan', don_id=don_moi.id) 
        
    return render(request, 'map_app/booking.html', {'phong': phong_duoc_chon})

@login_required
def thanh_toan(request, don_id):
    don = get_object_or_404(DonDatPhong, id=don_id, nguoi_thue=request.user)
    if request.method == 'POST':
        don.trang_thai = 'da_dat_coc' 
        don.save()
        messages.success(request, "Đã gửi xác nhận thanh toán! Admin sẽ liên hệ bạn sớm.")
        return redirect('home')
    noi_dung_ck = f"DAT COC PHONG {don.phong.id}"
    qr_url = f"https://img.vietqr.io/image/Sacombank-060308333003-compact.jpg?amount={int(don.tien_coc)}&addInfo={noi_dung_ck}&accountName=CHU_TRO"
    return render(request, 'map_app/payment.html', {'don': don, 'qr_url': qr_url})

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

        range_val = (input_val / 60) * van_toc * 1000 if mode == 'time' else input_val * 1000
        range_type = 'distance'

        headers = {'Authorization': ORS_API_KEY.strip(), 'Content-Type': 'application/json'}
        body = {"locations": [[lng, lat]], "range": [range_val], "range_type": range_type, "attributes": ["area"]}
        
        response = requests.post("https://api.openrouteservice.org/v2/isochrones/driving-car", json=body, headers=headers)
        
        if response.status_code != 200:
            return JsonResponse({'error': 'Lỗi API ORS'}, status=400)

        data = response.json()
        if 'features' in data:
            poly = GEOSGeometry(json.dumps(data['features'][0]['geometry']))
            nha_tros = NhaTro.objects.filter(location__within=poly)
            results = []
            for nha in nha_tros:
                phong_trong = nha.danh_sach_phong.filter(trang_thai='trong')
                if phong_trong.exists():
                    img_url = nha.hinh_anh.url if nha.hinh_anh else ""
                    phong_re_nhat = phong_trong.order_by('gia_thue').first()
                    results.append({
                        'id': nha.id, 
                        'ten': nha.ten_nha,
                        'gia': phong_re_nhat.gia_thue,
                        'dia_chi': nha.dia_chi, 
                        'lat': nha.location.y, 
                        'lng': nha.location.x, 
                        'img': img_url
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
        nha = get_object_or_404(NhaTro, pk=pk)
        if request.user in nha.favorites.all():
            nha.favorites.remove(request.user)
            liked = False
        else:
            nha.favorites.add(request.user)
            liked = True
        return JsonResponse({'success': True, 'liked': liked})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def gui_danh_gia(request, room_id):
    if request.method == 'POST':
        nha = get_object_or_404(NhaTro, id=room_id)
        da_danh_gia = DanhGia.objects.filter(nha_tro=nha, nguoi_danh_gia=request.user).exists()
        
        if da_danh_gia:
            messages.error(request, "❌ Bạn đã đánh giá khu trọ này rồi!")
        else:
            DanhGia.objects.create(
                nha_tro=nha,
                nguoi_danh_gia=request.user,
                so_sao=request.POST.get('so_sao'),
                noi_dung=request.POST.get('noi_dung')
            )
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá!")
    return redirect('room_detail', pk=room_id)

def yeu_cau_dang_ky(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email này đã được sử dụng. Vui lòng đăng nhập!")
                return redirect('login')

            token = signer.sign(email)
            link = request.build_absolute_uri(reverse('xac_nhan_dang_ky', args=[token]))
            subject = 'Link xác nhận đăng ký tài khoản SmartRent 🏠'
            html_message = render_to_string('map_app/emails/register_link_email.html', {'link': link})
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(subject, plain_message, 'SmartRent <noreply@smartrent.vn>', [email], html_message=html_message)
                messages.success(request, "Tuyệt vời! Vui lòng kiểm tra email (Mailtrap) để lấy link đăng ký.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Lỗi gửi mail: {e}")
                
    return render(request, 'map_app/yeu_cau_dang_ky.html')

def xac_nhan_dang_ky(request, token):
    try:
        email = signer.unsign(token, max_age=900)
    except SignatureExpired:
        messages.error(request, "Link đăng ký đã hết hạn (quá 15 phút). Vui lòng gửi lại yêu cầu.")
        return redirect('register')
    except BadSignature:
        messages.error(request, "Link đăng ký không hợp lệ hoặc đã bị chỉnh sửa.")
        return redirect('register')

    if request.method == 'POST':
        form = DangKyForm(request.POST) 
        if form.is_valid():
            user = form.save(commit=False)
            user.email = email
            user.save()
            messages.success(request, "Đăng ký thành công! Chào mừng bạn đến với SmartRent.")
            return redirect('login')
    else:
        form = DangKyForm(initial={'email': email})

    return render(request, 'map_app/register.html', {'form': form, 'email_verified': email})

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
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    return redirect('home')

@login_required
def saved_rooms(request):
    saved_list = request.user.nha_tro_yeu_thich.all()
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
    return render(request, 'map_app/profile.html', {'u_form': u_form})

@login_required
def booking_history(request):
    history = DonDatPhong.objects.filter(nguoi_thue=request.user).order_by('-ngay_tao')
    return render(request, 'map_app/booking_history.html', {'history': history})

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
    return render(request, 'map_app/pages/complaint.html')

@login_required
def lich_su_khieu_nai(request):
    danh_sach = KhieuNai.objects.filter(nguoi_gui=request.user).order_by('-ngay_tao')
    return render(request, 'map_app/complaint_history.html', {'danh_sach': danh_sach})

def news_list(request):
    return render(request, 'map_app/news_list.html', {'news': TinTuc.objects.order_by('-ngay_dang')})

def news_detail(request, pk):
    item = get_object_or_404(TinTuc, pk=pk)
    related = TinTuc.objects.exclude(pk=pk).order_by('-ngay_dang')[:5]
    return render(request, 'map_app/news_detail.html', {'news': item, 'related_news': related})

def guide(request): return render(request, 'map_app/pages/guide.html')
def privacy(request): return render(request, 'map_app/pages/privacy.html')
def faq(request): return render(request, 'map_app/pages/faq.html')
def gioi_thieu(request):
    noi_dung = TrangGioiThieu.load()
    return render(request, 'map_app/pages/gioi_thieu.html', {'nd': noi_dung})

@admin_only
def admin_dashboard(request):
    tong_nha = NhaTro.objects.count()
    tong_don = DonDatPhong.objects.count()
    don_cho_duyet = DonDatPhong.objects.filter(trang_thai='cho_xac_nhan').count() 
    tong_khieu_nai = KhieuNai.objects.count()
    khieu_nai_chua_xu_ly = KhieuNai.objects.filter(trang_thai='moi').count()
    tong_user = User.objects.filter(is_superuser=False).count() 
    don_moi_nhat = DonDatPhong.objects.all().order_by('-id')[:5]

    context = {
        'tong_phong': tong_nha,
        'tong_don': tong_don,
        'don_cho_duyet': don_cho_duyet,
        'tong_khieu_nai': tong_khieu_nai,
        'khieu_nai_chua_xu_ly': khieu_nai_chua_xu_ly,
        'tong_user': tong_user,
        'don_moi_nhat': don_moi_nhat,
    }
    return render(request, 'map_app/admin_custom/admin_dashboard.html', context)

@admin_only
def custom_admin_users(request):
    queryset = User.objects.all().order_by('-date_joined')
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'map_app/admin_custom/user_list.html', {'danh_sach_user': page_obj})

@admin_only
def custom_admin_khoa_user(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user: messages.error(request, "Không thể tự khóa tài khoản!")
    else:
        user_obj.is_active = not user_obj.is_active 
        user_obj.save()
        messages.success(request, f"Đã {'MỞ KHÓA' if user_obj.is_active else 'KHÓA'} tài khoản của {user_obj.username}!")
    return redirect('custom_admin_users')

@admin_only
def custom_admin_xoa_user(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user: messages.error(request, "Không thể tự xóa tài khoản!")
    else:
        user_obj.delete()
        messages.success(request, f"Đã xóa vĩnh viễn {user_obj.username}!")
    return redirect('custom_admin_users')

@admin_only
def custom_admin_edit_user(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user_obj.first_name, user_obj.last_name, user_obj.email = request.POST.get('first_name'), request.POST.get('last_name'), request.POST.get('email')
        new_pw = request.POST.get('new_password')
        if new_pw: user_obj.set_password(new_pw) 
        user_obj.save() 
        messages.success(request, f"Đã cập nhật {user_obj.username}!")
        return redirect('custom_admin_users')
    return render(request, 'map_app/admin_custom/user_edit.html', {'user_obj': user_obj})

@admin_only
def admin_cap_quyen_chu_tro(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        so_dt  = request.POST.get('so_dien_thoai', '')
        dc     = request.POST.get('dia_chi', '')
        ghi_chu = request.POST.get('ghi_chu', '')
 
        HoSoChuTro.objects.update_or_create(
            user=user_obj,
            defaults={'so_dien_thoai': so_dt, 'dia_chi': dc, 'ghi_chu': ghi_chu}
        )
        messages.success(request, f'✅ Đã cấp quyền Chủ trọ cho {user_obj.username}!')
        return redirect('custom_admin_users')
 
    ho_so = getattr(user_obj, 'ho_so_chu_tro', None)
    return render(request, 'map_app/admin_custom/cap_quyen_chu_tro.html', {
        'user_obj': user_obj,
        'ho_so': ho_so,
    })
 
@admin_only
def admin_thu_hoi_quyen_chu_tro(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    HoSoChuTro.objects.filter(user=user_obj).delete()
    messages.success(request, f'🔒 Đã thu hồi quyền Chủ trọ của {user_obj.username}!')
    return redirect('custom_admin_users')

@admin_only
def custom_admin_phongtro(request):
    queryset = NhaTro.objects.all().order_by('-created_at')
    for p in queryset: 
        p.ten = p.ten_nha
        phong_re = p.danh_sach_phong.order_by('gia_thue').first()
        p.gia_thap_nhat = phong_re.gia_thue if phong_re else 0
    
    paginator = Paginator(queryset, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'map_app/admin_custom/phongtro_list.html', {'danh_sach_phong': page_obj})

@admin_only
def custom_admin_xoa_phongtro(request, pk):
    phong = get_object_or_404(NhaTro, pk=pk)
    phong.delete() 
    messages.success(request, "Đã xóa thành công!")
    return redirect('custom_admin_phongtro')

@admin_only
def custom_admin_them_phongtro(request):
    if request.method == 'POST':
        ten     = request.POST.get('ten')
        dia_chi = request.POST.get('dia_chi')
        mo_ta   = request.POST.get('mo_ta')
        lat, lng = request.POST.get('lat'), request.POST.get('lng')
        location = Point(float(lng), float(lat), srid=4326) if lat and lng else None

        nha_moi = NhaTro.objects.create(
            ten_nha=ten, dia_chi=dia_chi, mo_ta=mo_ta,
            hinh_anh=request.FILES.get('hinh_anh'), location=location
        )
        for f in request.FILES.getlist('hinh_anh_phu'):
            HinhAnhNhaTro.objects.create(nha_tro=nha_moi, hinh_anh=f)

        phong_count = int(request.POST.get('phong_count', 0))
        for i in range(phong_count):
            ten_p = request.POST.get(f'phong_ten_{i}')
            if not ten_p:
                continue
            PhongTro.objects.create(
                nha_tro    = nha_moi,
                ten_phong  = ten_p,
                gia_thue   = request.POST.get(f'phong_gia_{i}', 0),
                dien_tich  = request.POST.get(f'phong_dien_tich_{i}', 20),
                trang_thai = request.POST.get(f'phong_trang_thai_{i}', 'trong'),
                hinh_anh   = request.FILES.get(f'phong_hinh_anh_{i}'),
            )

        messages.success(request, "Thêm khu trọ mới thành công!")
        return redirect('custom_admin_phongtro')
    return render(request, 'map_app/admin_custom/phongtro_form.html', {'action': 'Thêm Mới'})

@admin_only
def custom_admin_sua_phongtro(request, pk):
    phong = get_object_or_404(NhaTro, pk=pk)
    phong.ten = phong.ten_nha
    if request.method == 'POST':
        phong.ten_nha = request.POST.get('ten')
        phong.dia_chi = request.POST.get('dia_chi')
        phong.mo_ta   = request.POST.get('mo_ta')
        lat, lng = request.POST.get('lat'), request.POST.get('lng')
        if lat and lng: phong.location = Point(float(lng), float(lat), srid=4326)
        if 'hinh_anh' in request.FILES: phong.hinh_anh = request.FILES['hinh_anh']
        phong.save()
        for f in request.FILES.getlist('hinh_anh_phu'):
            HinhAnhNhaTro.objects.create(nha_tro=phong, hinh_anh=f)

        phong_count = int(request.POST.get('phong_count', 0))
        for i in range(phong_count):
            ten_p = request.POST.get(f'phong_ten_{i}')
            if not ten_p:
                continue
            PhongTro.objects.create(
                nha_tro    = phong,
                ten_phong  = ten_p,
                gia_thue   = request.POST.get(f'phong_gia_{i}', 0),
                dien_tich  = request.POST.get(f'phong_dien_tich_{i}', 20),
                trang_thai = request.POST.get(f'phong_trang_thai_{i}', 'trong'),
                hinh_anh   = request.FILES.get(f'phong_hinh_anh_{i}'),
            )

        messages.success(request, "Đã cập nhật khu trọ!")
        return redirect('custom_admin_phongtro')
    return render(request, 'map_app/admin_custom/phongtro_form.html',
                  {'action': 'Chỉnh Sửa', 'phong': phong})

@chu_tro_required
def custom_admin_sua_phong_con(request, pk):
    phong = get_object_or_404(PhongTro, pk=pk)
    if not request.user.is_superuser and phong.nha_tro.owner != request.user:
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền sửa phòng này!'})

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        phong.ten_phong  = request.POST.get('ten_phong',  phong.ten_phong)
        phong.gia_thue   = request.POST.get('gia_thue',   phong.gia_thue)
        phong.dien_tich  = request.POST.get('dien_tich',  phong.dien_tich)
        phong.trang_thai = request.POST.get('trang_thai', phong.trang_thai)

        if 'hinh_anh' in request.FILES and request.FILES['hinh_anh']:
            phong.hinh_anh = request.FILES['hinh_anh']

        phong.save()
        
        anh_url = phong.hinh_anh.url if phong.hinh_anh else ''
        return JsonResponse({'success': True, 'anh_url': anh_url})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@chu_tro_required  
def custom_admin_xoa_phong_con(request, pk):
    try:
        phong = get_object_or_404(PhongTro, pk=pk)
        if not request.user.is_superuser and phong.nha_tro.owner != request.user:
            return JsonResponse({'success': False, 'error': 'Bạn không có quyền xóa phòng này!'})
        
        phong.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@chu_tro_required
def custom_admin_xoa_anh_daidien(request, pk):
    try:
        phong = get_object_or_404(NhaTro, pk=pk)
        if not request.user.is_superuser and phong.owner != request.user:
            return JsonResponse({'success': False, 'error': 'Từ chối quyền truy cập!'})

        if phong.hinh_anh:
            phong.hinh_anh.delete(save=False) 
            phong.hinh_anh = None 
            phong.save()
        return JsonResponse({'success': True})
    except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

@chu_tro_required
def custom_admin_xoa_anh_phongtro(request, anh_id):
    try:
        anh = get_object_or_404(HinhAnhNhaTro, pk=anh_id)
        if not request.user.is_superuser and anh.nha_tro.owner != request.user:
            return JsonResponse({'success': False, 'error': 'Từ chối quyền truy cập!'})

        anh.delete()
        return JsonResponse({'success': True})
    except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

@admin_only
def custom_admin_tintuc(request):
    queryset = TinTuc.objects.all().order_by('-ngay_dang')
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'map_app/admin_custom/tintuc_list.html', {'danh_sach_tin': page_obj})

@admin_only
def custom_admin_them_tintuc(request):
    if request.method == 'POST':
        tin = TinTuc.objects.create(tieu_de=request.POST.get('tieu_de'), noi_dung=request.POST.get('noi_dung'), hinh_anh=request.FILES.get('hinh_anh'))
        for file_anh in request.FILES.getlist('hinh_anh_phu'): HinhAnhTinTuc.objects.create(tin_tuc=tin, hinh_anh=file_anh)
        messages.success(request, "Thêm bài viết mới thành công!")
        return redirect('custom_admin_tintuc')
    return render(request, 'map_app/admin_custom/tintuc_form.html', {'action': 'Thêm Mới'})

@admin_only
def custom_admin_sua_tintuc(request, pk):
    tin = get_object_or_404(TinTuc, pk=pk)
    if request.method == 'POST':
        tin.tieu_de, tin.noi_dung = request.POST.get('tieu_de'), request.POST.get('noi_dung')
        if 'hinh_anh' in request.FILES: tin.hinh_anh = request.FILES['hinh_anh']
        tin.save()
        for file_anh in request.FILES.getlist('hinh_anh_phu'): HinhAnhTinTuc.objects.create(tin_tuc=tin, hinh_anh=file_anh)
        messages.success(request, "Đã cập nhật!")
        return redirect('custom_admin_tintuc')
    return render(request, 'map_app/admin_custom/tintuc_form.html', {'action': 'Chỉnh Sửa', 'tin_tuc': tin})

@admin_only
def custom_admin_xoa_tintuc(request, pk):
    get_object_or_404(TinTuc, pk=pk).delete()
    messages.success(request, "Đã xóa bài viết thành công!")
    return redirect('custom_admin_tintuc')

@admin_only
def custom_admin_xoa_anh_daidien_tintuc(request, pk):
    try:
        tin = get_object_or_404(TinTuc, pk=pk)
        if tin.hinh_anh:
            tin.hinh_anh.delete(save=False)
            tin.hinh_anh = None
            tin.save()
        return JsonResponse({'success': True})
    except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

@admin_only
def custom_admin_xoa_anh_phu_tintuc(request, anh_id):
    try:
        get_object_or_404(HinhAnhTinTuc, pk=anh_id).delete()
        return JsonResponse({'success': True})
    except Exception as e: return JsonResponse({'success': False, 'error': str(e)})

@admin_only
def custom_admin_dondatphong(request):
    queryset = DonDatPhong.objects.all().order_by('-ngay_tao')
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'map_app/admin_custom/dondatphong_list.html', {'danh_sach_don': page_obj})

@admin_only
def custom_admin_duyet_don(request, pk):
    don = get_object_or_404(DonDatPhong, pk=pk)
    if request.method == 'POST':
        don.trang_thai = request.POST.get('trang_thai')
        don.save()
        messages.success(request, "Đã cập nhật trạng thái đơn!")
    return redirect('custom_admin_dondatphong')

@admin_only
def custom_admin_xoa_don(request, pk):
    get_object_or_404(DonDatPhong, pk=pk).delete()
    messages.success(request, "Đã xóa đơn đặt phòng!")
    return redirect('custom_admin_dondatphong')

@admin_only
def custom_admin_khieunai(request):
    queryset = KhieuNai.objects.all().order_by('-ngay_tao')
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'map_app/admin_custom/khieunai_list.html', {'danh_sach': page_obj})

@admin_only
def custom_admin_cap_nhat_khieunai(request, pk):
    kn = get_object_or_404(KhieuNai, pk=pk)
    if request.method == 'POST':
        kn.trang_thai = request.POST.get('trang_thai')
        kn.save()
        messages.success(request, "Đã cập nhật trạng thái khiếu nại!")
    return redirect('custom_admin_khieunai')

@admin_only
def admin_gioi_thieu(request):
    noi_dung = TrangGioiThieu.load()
    if request.method == 'POST':
        noi_dung.tieu_de_chinh  = request.POST.get('tieu_de_chinh', noi_dung.tieu_de_chinh)
        noi_dung.mo_ta_ngan     = request.POST.get('mo_ta_ngan',    noi_dung.mo_ta_ngan)
        if 'hinh_anh_banner' in request.FILES:
            noi_dung.hinh_anh_banner = request.FILES['hinh_anh_banner']

        noi_dung.tieu_de_su_menh  = request.POST.get('tieu_de_su_menh',  noi_dung.tieu_de_su_menh)
        noi_dung.noi_dung_su_menh = request.POST.get('noi_dung_su_menh', noi_dung.noi_dung_su_menh)

        noi_dung.so_phong     = int(request.POST.get('so_phong',     0) or 0)
        noi_dung.so_sinh_vien = int(request.POST.get('so_sinh_vien', 0) or 0)
        noi_dung.so_quan      = int(request.POST.get('so_quan',      0) or 0)
        noi_dung.so_nam       = int(request.POST.get('so_nam',       0) or 0)

        for i in [1, 2, 3]:
            setattr(noi_dung, f'thanh_vien_{i}_ten', request.POST.get(f'thanh_vien_{i}_ten', ''))
            setattr(noi_dung, f'thanh_vien_{i}_chuc_vu', request.POST.get(f'thanh_vien_{i}_chuc_vu', ''))
            if f'thanh_vien_{i}_anh' in request.FILES:
                setattr(noi_dung, f'thanh_vien_{i}_anh', request.FILES[f'thanh_vien_{i}_anh'])

        noi_dung.email          = request.POST.get('email',          '')
        noi_dung.so_dien_thoai  = request.POST.get('so_dien_thoai',  '')
        noi_dung.dia_chi        = request.POST.get('dia_chi',        '')
        noi_dung.facebook       = request.POST.get('facebook',       '')
        noi_dung.zalo           = request.POST.get('zalo',           '')

        noi_dung.save()
        messages.success(request, '✅ Đã cập nhật trang Giới thiệu thành công!')
        return redirect('admin_gioi_thieu')
    return render(request, 'map_app/admin_custom/gioi_thieu_form.html', {'nd': noi_dung})

@chu_tro_required
def chu_tro_dashboard(request):
    if request.user.is_superuser:
        nha_list = NhaTro.objects.all()
    else:
        nha_list = NhaTro.objects.filter(owner=request.user)
 
    tong_phong   = sum(n.danh_sach_phong.count() for n in nha_list)
    phong_trong  = sum(n.danh_sach_phong.filter(trang_thai='trong').count() for n in nha_list)
    don_cho      = DonDatPhong.objects.filter(phong__nha_tro__in=nha_list, trang_thai='cho_xac_nhan').count()
 
    return render(request, 'map_app/chu_tro/dashboard.html', {
        'nha_list':    nha_list,
        'tong_nha':    nha_list.count(),
        'tong_phong':  tong_phong,
        'phong_trong': phong_trong,
        'don_cho':     don_cho,
    })

@chu_tro_required
def chu_tro_danh_sach_phongtro(request):
    if request.user.is_superuser:
        ds = NhaTro.objects.all().order_by('-created_at')
    else:
        ds = NhaTro.objects.filter(owner=request.user).order_by('-created_at')
        
    for n in ds:
        n.ten = n.ten_nha
        phong_re = n.danh_sach_phong.order_by('gia_thue').first()
        n.gia_thap_nhat = phong_re.gia_thue if phong_re else 0
        
    paginator = Paginator(ds, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'map_app/chu_tro/phongtro_list.html', {'danh_sach_phong': page_obj})
 
@chu_tro_required
def chu_tro_them_phongtro(request):
    if request.method == 'POST':
        ten     = request.POST.get('ten')
        dia_chi = request.POST.get('dia_chi')
        mo_ta   = request.POST.get('mo_ta')
        lat, lng = request.POST.get('lat'), request.POST.get('lng')
        location = Point(float(lng), float(lat), srid=4326) if lat and lng else None
 
        nha_moi = NhaTro.objects.create(
            ten_nha=ten, dia_chi=dia_chi, mo_ta=mo_ta,
            hinh_anh=request.FILES.get('hinh_anh'),
            location=location,
            owner=request.user,
        )
        for f in request.FILES.getlist('hinh_anh_phu'):
            HinhAnhNhaTro.objects.create(nha_tro=nha_moi, hinh_anh=f)
 
        phong_count = int(request.POST.get('phong_count', 0))
        for i in range(phong_count):
            ten_p = request.POST.get(f'phong_ten_{i}')
            if not ten_p:
                continue
            PhongTro.objects.create(
                nha_tro=nha_moi,
                ten_phong=ten_p,
                gia_thue=request.POST.get(f'phong_gia_{i}', 0),
                dien_tich=request.POST.get(f'phong_dien_tich_{i}', 20),
                trang_thai=request.POST.get(f'phong_trang_thai_{i}', 'trong'),
                hinh_anh=request.FILES.get(f'phong_hinh_anh_{i}'),
            )
        messages.success(request, "Thêm khu trọ mới thành công!")
        return redirect('chu_tro_danh_sach_phongtro')
 
    return render(request, 'map_app/chu_tro/phongtro_form.html', {'action': 'Thêm Mới', 'back_url': 'chu_tro_danh_sach_phongtro'})
 
@chu_tro_required
def chu_tro_sua_phongtro(request, pk):
    nha = get_object_or_404(NhaTro, pk=pk)
    if not request.user.is_superuser and nha.owner != request.user:
        raise PermissionDenied("Bạn không có quyền chỉnh sửa khu trọ này!")
 
    nha.ten = nha.ten_nha
    if request.method == 'POST':
        nha.ten_nha = request.POST.get('ten')
        nha.dia_chi = request.POST.get('dia_chi')
        nha.mo_ta   = request.POST.get('mo_ta')
        lat, lng = request.POST.get('lat'), request.POST.get('lng')
        if lat and lng:
            nha.location = Point(float(lng), float(lat), srid=4326)
        if 'hinh_anh' in request.FILES:
            nha.hinh_anh = request.FILES['hinh_anh']
        nha.save()
        for f in request.FILES.getlist('hinh_anh_phu'):
            HinhAnhNhaTro.objects.create(nha_tro=nha, hinh_anh=f)
 
        phong_count = int(request.POST.get('phong_count', 0))
        for i in range(phong_count):
            ten_p = request.POST.get(f'phong_ten_{i}')
            if not ten_p:
                continue
            PhongTro.objects.create(
                nha_tro=nha,
                ten_phong=ten_p,
                gia_thue=request.POST.get(f'phong_gia_{i}', 0),
                dien_tich=request.POST.get(f'phong_dien_tich_{i}', 20),
                trang_thai=request.POST.get(f'phong_trang_thai_{i}', 'trong'),
                hinh_anh=request.FILES.get(f'phong_hinh_anh_{i}'),
            )
        messages.success(request, "Đã cập nhật khu trọ!")
        return redirect('chu_tro_danh_sach_phongtro')
 
    return render(request, 'map_app/chu_tro/phongtro_form.html', {'action': 'Chỉnh Sửa', 'phong': nha, 'back_url': 'chu_tro_danh_sach_phongtro'})
 
@chu_tro_required
def chu_tro_xoa_phongtro(request, pk):
    nha = get_object_or_404(NhaTro, pk=pk)
    if not request.user.is_superuser and nha.owner != request.user:
        raise PermissionDenied("Bạn không có quyền xóa khu trọ này!")
    nha.delete()
    messages.success(request, "Đã xóa khu trọ!")
    return redirect('chu_tro_danh_sach_phongtro')

@chu_tro_required
def chu_tro_don_dat_phong(request):
    if request.user.is_superuser:
        ds = DonDatPhong.objects.all().order_by('-ngay_tao')
    else:
        nha_list = NhaTro.objects.filter(owner=request.user)
        ds = DonDatPhong.objects.filter(phong__nha_tro__in=nha_list).order_by('-ngay_tao')
    paginator = Paginator(ds, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'map_app/chu_tro/don_dat_phong.html', {'danh_sach_don': page_obj})
 
@chu_tro_required
def chu_tro_duyet_don(request, pk):
    don = get_object_or_404(DonDatPhong, pk=pk)
    if not request.user.is_superuser and don.phong.nha_tro.owner != request.user:
        raise PermissionDenied("Bạn không có quyền duyệt đơn này!")
        
    if request.method == 'POST':
        trang_thai_moi = request.POST.get('trang_thai')
        don.trang_thai = trang_thai_moi
        don.save()
        
        if trang_thai_moi == 'huy' or trang_thai_moi == 'tu_choi':
            don.phong.trang_thai = 'trong'
            don.phong.save()
        elif trang_thai_moi == 'da_duyet' or trang_thai_moi == 'thanh_cong':
            don.phong.trang_thai = 'da_thue'
            don.phong.save()

        messages.success(request, "Đã cập nhật trạng thái đơn!")
    return redirect('chu_tro_don_dat_phong')

@chu_tro_required
def chu_tro_xoa_don(request, pk):
    don = get_object_or_404(DonDatPhong, pk=pk)
    if not request.user.is_superuser and don.phong.nha_tro.owner != request.user:
        raise PermissionDenied("Bạn không có quyền xóa đơn này!")
    don.delete()
    messages.success(request, "Đã xóa đơn đặt phòng!")
    return redirect('chu_tro_don_dat_phong')