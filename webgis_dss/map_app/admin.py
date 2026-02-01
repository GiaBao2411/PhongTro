# map_app/admin.py
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import PhongTro, TinTuc
from django.utils.html import mark_safe

# Hàm chung để hiển thị ảnh xem trước (Dùng cho cả 2 bên)
def get_hinh_anh_preview(obj):
    if obj.hinh_anh:
        # Hiển thị ảnh nhỏ kích thước 80px
        return mark_safe(f'<img src="{obj.hinh_anh.url}" style="width: 80px; height:auto; border-radius: 5px; border: 1px solid #ddd;" />')
    return mark_safe('<span style="color: #999;">(Chưa có ảnh)</span>')

# 1. Cấu hình cho PHÒNG TRỌ
class PhongTroAdmin(OSMGeoAdmin):
    list_display = ('ten', 'hinh_anh_preview', 'gia_thue', 'dia_chi', 'created_at')
    search_fields = ('ten', 'dia_chi')
    list_filter = ('gia_thue',)
    readonly_fields = ('hinh_anh_preview',) # Hiển thị ảnh trong trang sửa chi tiết

    def hinh_anh_preview(self, obj):
        return get_hinh_anh_preview(obj)
    hinh_anh_preview.short_description = "Ảnh phòng"

# 2. Cấu hình cho TIN TỨC (Đã thêm phần ảnh)
class TinTucAdmin(admin.ModelAdmin):
    # Thêm 'hinh_anh_preview' vào danh sách hiển thị
    list_display = ('tieu_de', 'hinh_anh_preview', 'ngay_dang')
    search_fields = ('tieu_de',)
    list_filter = ('ngay_dang',)
    
    # Hiển thị ảnh xem trước ngay trong form sửa, bên trên ô chọn file
    readonly_fields = ('hinh_anh_preview',) 
    fields = ('tieu_de', 'hinh_anh_preview', 'hinh_anh', 'noi_dung')

    # Hàm hiển thị ảnh nhỏ cho tin tức
    def hinh_anh_preview(self, obj):
        return get_hinh_anh_preview(obj)
    hinh_anh_preview.short_description = "Ảnh đại diện"

# Đăng ký vào trang Admin
admin.site.register(PhongTro, PhongTroAdmin)
admin.site.register(TinTuc, TinTucAdmin)