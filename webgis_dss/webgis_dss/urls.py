from django.contrib import admin
from django.urls import path
from map_app import views  # Import view từ app của bạn

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Đường dẫn trang chủ (vào web là thấy map luôn)
    path('', views.index, name='home'),
    
    # Đường dẫn ngầm để tìm kiếm
    path('api/tim-kiem/', views.search_api, name='search_api'),
]