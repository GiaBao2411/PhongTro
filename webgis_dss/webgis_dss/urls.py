from django.contrib import admin
from django.urls import path
from map_app import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('ban-do/', views.map_view, name='map_view'),
    path('danh-sach-phong/', views.room_list, name='room_list'), 
    path('phong-tro/<int:pk>/', views.room_detail, name='room_detail'),
    path('tin-tuc/', views.news_list, name='news_list'),         
    path('tin-tuc/<int:pk>/', views.news_detail, name='news_detail'),
    
    path('huong-dan/', views.guide, name='guide'),
    path('chinh-sach-bao-mat/', views.privacy, name='privacy'),
    path('cau-hoi-thuong-gap/', views.faq, name='faq'),

    path('dang-ky/', views.yeu_cau_dang_ky, name='dang_ky'), # Bước 1: Nhập email
    path('xac-nhan-dang-ky/<str:token>/', views.xac_nhan_dang_ky, name='xac_nhan_dang_ky'), # Bước 2: Click link
    path('dang-nhap/', auth_views.LoginView.as_view(template_name='map_app/login.html'), name='login'),
    path('dang-xuat/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('login-success/', views.login_success, name='login_success'),
    
    path('tai-khoan/', views.profile, name='profile'),
    path('doi-mat-khau/', auth_views.PasswordChangeView.as_view(template_name='map_app/change_password.html', success_url='/tai-khoan/'), name='change_password'),
    path('phong-da-luu/', views.saved_rooms, name='saved_rooms'),
    path('lich-su-dat-phong/', views.booking_history, name='booking_history'),
    path('lich-su-khieu-nai/', views.lich_su_khieu_nai, name='lich_su_khieu_nai'),

    path('dat-phong/<int:room_id>/', views.xac_nhan_dat_phong, name='dat_phong'),
    path('thanh-toan/<int:don_id>/', views.thanh_toan, name='thanh_toan'),
    path('phong-tro/<int:room_id>/gui-danh-gia/', views.gui_danh_gia, name='gui_danh_gia'),
    path('khieu-nai/', views.gui_khieu_nai, name='gui_khieu_nai'),
    path('giai-quyet-khieu-nai/', views.gui_khieu_nai, name='complaint'),

    path('api/tim-kiem/', views.search_api, name='search_api'), 
    path('api/dan-duong/', views.route_api, name='route_api'),
    path('api/toggle-favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),

    path('he-thong/', views.admin_dashboard, name='admin_dashboard'),
    
    path('he-thong/nguoi-dung/', views.custom_admin_users, name='custom_admin_users'),
    path('he-thong/nguoi-dung/khoa/<int:pk>/', views.custom_admin_khoa_user, name='custom_admin_khoa_user'),
    path('he-thong/nguoi-dung/xoa/<int:pk>/', views.custom_admin_xoa_user, name='custom_admin_xoa_user'),
    path('he-thong/nguoi-dung/sua/<int:pk>/', views.custom_admin_edit_user, name='custom_admin_edit_user'),
    
    path('he-thong/phong-tro/', views.custom_admin_phongtro, name='custom_admin_phongtro'),
    path('he-thong/phong-tro/them/', views.custom_admin_them_phongtro, name='custom_admin_them_phongtro'),
    path('he-thong/phong-tro/sua/<int:pk>/', views.custom_admin_sua_phongtro, name='custom_admin_sua_phongtro'),
    path('he-thong/phong-tro/xoa/<int:pk>/', views.custom_admin_xoa_phongtro, name='custom_admin_xoa_phongtro'),
    path('admin-custom/phongtro/<int:pk>/xoa-anh-daidien/', views.custom_admin_xoa_anh_daidien, name='custom_admin_xoa_anh_daidien'),
    path('admin-custom/phongtro/xoa-anh/<int:anh_id>/', views.custom_admin_xoa_anh_phongtro, name='custom_admin_xoa_anh_phongtro'),
    
    path('he-thong/tin-tuc/', views.custom_admin_tintuc, name='custom_admin_tintuc'),
    path('he-thong/tin-tuc/them/', views.custom_admin_them_tintuc, name='custom_admin_them_tintuc'),
    path('he-thong/tin-tuc/sua/<int:pk>/', views.custom_admin_sua_tintuc, name='custom_admin_sua_tintuc'),
    path('he-thong/tin-tuc/xoa/<int:pk>/', views.custom_admin_xoa_tintuc, name='custom_admin_xoa_tintuc'),
    path('admin-custom/tintuc/<int:pk>/xoa-anh-daidien/', views.custom_admin_xoa_anh_daidien_tintuc, name='custom_admin_xoa_anh_daidien_tintuc'),
    path('admin-custom/tintuc/xoa-anh/<int:anh_id>/', views.custom_admin_xoa_anh_phu_tintuc, name='custom_admin_xoa_anh_phu_tintuc'),

    path('he-thong/don-dat-phong/', views.custom_admin_dondatphong, name='custom_admin_dondatphong'),
    path('he-thong/don-dat-phong/duyet/<int:pk>/', views.custom_admin_duyet_don, name='custom_admin_duyet_don'),
    path('he-thong/don-dat-phong/xoa/<int:pk>/', views.custom_admin_xoa_don, name='custom_admin_xoa_don'),
    
    path('he-thong/khieu-nai/', views.custom_admin_khieunai, name='custom_admin_khieunai'),
    path('he-thong/khieu-nai/cap-nhat/<int:pk>/', views.custom_admin_cap_nhat_khieunai, name='custom_admin_cap_nhat_khieunai'),

    path('gioi-thieu/', views.gioi_thieu, name='gioi_thieu'),
    path('admin-custom/phong/<int:pk>/sua/',  views.custom_admin_sua_phong_con,  name='custom_admin_sua_phong_con'),
    path('admin-custom/phong/<int:pk>/xoa/',  views.custom_admin_xoa_phong_con,  name='custom_admin_xoa_phong_con'),
    path('admin/', admin.site.urls),

    path('doi-mat-khau/', auth_views.PasswordChangeView.as_view(
            template_name='map_app/auth/doi_mat_khau.html',
            success_url='/' 
        ), name='doi_mat_khau'),
        path('quen-mat-khau/', auth_views.PasswordResetView.as_view(
            template_name='map_app/auth/quen_mat_khau.html',
            email_template_name='map_app/auth/email_quen_mat_khau.html', 
            subject_template_name='map_app/auth/email_subject.txt',
            success_url='/quen-mat-khau/da-gui/'
        ), name='quen_mat_khau'),
        path('quen-mat-khau/da-gui/', auth_views.PasswordResetDoneView.as_view(
            template_name='map_app/auth/quen_mat_khau_da_gui.html'
        ), name='password_reset_done'),
        path('dat-lai-mat-khau/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
            template_name='map_app/auth/dat_lai_mat_khau.html',
            success_url='/dat-lai-mat-khau/thanh-cong/'
        ), name='password_reset_confirm'),
        path('dat-lai-mat-khau/thanh-cong/', auth_views.PasswordResetCompleteView.as_view(
            template_name='map_app/auth/dat_lai_mat_khau_thanh_cong.html'
        ), name='password_reset_complete'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)