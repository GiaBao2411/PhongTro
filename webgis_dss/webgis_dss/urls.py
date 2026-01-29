from django.contrib import admin
from django.urls import path
from map_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # TRANG CHỦ (Vào web là thấy trang giới thiệu)
    path('', views.home, name='home'),
    
    # TRANG BẢN ĐỒ (Bấm menu mới vào đây)
    path('ban-do/', views.map_view, name='map_view'),
    
    # Trang chi tiết
    path('phong-tro/<int:pk>/', views.room_detail, name='room_detail'),
    
    # API
    path('api/tim-kiem/', views.search_api, name='search_api'),
    path('api/dan-duong/', views.route_api, name='route_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)