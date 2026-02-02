from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import PhongTro, TinTuc
from django.utils.html import mark_safe

# Hàm hiển thị ảnh (Giữ nguyên)
def get_hinh_anh_preview(obj):
    if obj.hinh_anh:
        return mark_safe(f'<img src="{obj.hinh_anh.url}" style="width: 80px; height:auto; border-radius: 5px; border: 1px solid #ddd;" />')
    return mark_safe('<span style="color: #999;">(Chưa có ảnh)</span>')

class PhongTroAdmin(LeafletGeoAdmin): 
    list_display = ('ten', 'hinh_anh_preview', 'gia_thue', 'dia_chi', 'created_at')
    search_fields = ('ten', 'dia_chi')
    list_filter = ('gia_thue',)
    readonly_fields = ('hinh_anh_preview',)
    
    settings_overrides = {
       'DEFAULT_CENTER': (10.7769, 106.7009),
       'DEFAULT_ZOOM': 13,
    }

    def hinh_anh_preview(self, obj):
        return get_hinh_anh_preview(obj)
    hinh_anh_preview.short_description = "Ảnh phòng"

class TinTucAdmin(admin.ModelAdmin):
    list_display = ('tieu_de', 'hinh_anh_preview', 'ngay_dang')
    search_fields = ('tieu_de',)
    list_filter = ('ngay_dang',)
    readonly_fields = ('hinh_anh_preview',) 
    fields = ('tieu_de', 'hinh_anh_preview', 'hinh_anh', 'noi_dung')

    def hinh_anh_preview(self, obj):
        return get_hinh_anh_preview(obj)
    hinh_anh_preview.short_description = "Ảnh đại diện"

admin.site.register(PhongTro, PhongTroAdmin)
admin.site.register(TinTuc, TinTucAdmin)