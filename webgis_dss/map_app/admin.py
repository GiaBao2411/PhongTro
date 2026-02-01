from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import PhongTro, TinTuc
from django.utils.html import mark_safe

# 1. Cấu hình cho PHÒNG TRỌ (Có bản đồ & Hình ảnh)
class PhongTroAdmin(OSMGeoAdmin):
    list_display = ('ten', 'gia_thue', 'dia_chi', 'hinh_anh_preview', 'created_at')
    search_fields = ('ten', 'dia_chi')
    list_filter = ('gia_thue',)
    
    # Hàm hiển thị ảnh nhỏ
    def hinh_anh_preview(self, obj):
        if obj.hinh_anh:
            return mark_safe(f'<img src="{obj.hinh_anh.url}" style="width: 60px; height:60px; object-fit:cover; border-radius: 5px;" />')
        return "Không có ảnh"
    hinh_anh_preview.short_description = "Hình ảnh"

# 2. Cấu hình cho TIN TỨC (Chỉ có Tiêu đề & Nội dung)
class TinTucAdmin(admin.ModelAdmin):
    # LƯU Ý: Không được đưa 'hinh_anh_preview' vào đây vì TinTuc không có ảnh
    list_display = ('tieu_de', 'ngay_dang')
    search_fields = ('tieu_de',)
    list_filter = ('ngay_dang',)

# Đăng ký vào trang Admin
admin.site.register(PhongTro, PhongTroAdmin)
admin.site.register(TinTuc, TinTucAdmin)