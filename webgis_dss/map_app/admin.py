from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import PhongTro

# Cấu hình để hiện bản đồ OpenStreetMap trong trang quản trị
@admin.register(PhongTro)
class PhongTroAdmin(OSMGeoAdmin):
    list_display = ('ten', 'gia_thue', 'dia_chi') # Hiện các cột này ra ngoài danh sách
    search_fields = ('ten', 'dia_chi')
    default_lon = 106.660172  # Kinh độ (TP.HCM)
    default_lat = 10.762622   # Vĩ độ (TP.HCM)
    default_zoom = 12         # Độ zoom vừa phải