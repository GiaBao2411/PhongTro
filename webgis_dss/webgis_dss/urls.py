from django.contrib import admin
from django.urls import path
from map_app import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- 1. CÁC TRANG HTML ---
    path('', views.home, name='home'),
    path('ban-do/', views.map_view, name='map_view'),
    path('phong-tro/<int:pk>/', views.room_detail, name='room_detail'),
    path('danh-sach-phong/', views.room_list, name='room_list'), # Trang danh sách tất cả phòng

    # --- 2. API (XỬ LÝ NGẦM) ---
    # Lưu ý: Đã đổi 'loc-phong' thành 'tim-kiem' để khớp với views.py mới
    path('api/tim-kiem/', views.search_api, name='search_api'), 
    path('api/dan-duong/', views.route_api, name='route_api'),
    path('api/toggle-favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),
    
    # --- 3. TÀI KHOẢN & ĐĂNG NHẬP ---
    path('dang-ky/', views.register, name='register'),
    path('dang-nhap/', auth_views.LoginView.as_view(template_name='map_app/login.html'), name='login'),
    path('dang-xuat/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('login-success/', views.login_success, name='login_success'),
    
    path('tai-khoan/', views.profile, name='profile'),
    path('phong-da-luu/', views.saved_rooms, name='saved_rooms'),
    
    # Đổi mật khẩu
    path('doi-mat-khau/', auth_views.PasswordChangeView.as_view(
        template_name='map_app/change_password.html',
        success_url='/tai-khoan/'
    ), name='change_password'),

    # --- 4. TIN TỨC ---
    path('tin-tuc/', views.news_list, name='news_list'),         
    path('tin-tuc/<int:pk>/', views.news_detail, name='news_detail'),
]

# Cấu hình load ảnh media khi đang chạy debug
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)