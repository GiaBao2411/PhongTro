from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import PhongTro, TinTuc
from django.utils.html import mark_safe
from .models import PhongTro, TinTuc, DonDatPhong
from django.contrib.gis.db import models as gis_models
from leaflet.forms.widgets import LeafletWidget
from django.urls import reverse


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

def duyet_don_hang(modeladmin, request, queryset):
    for don in queryset:
        # 1. Cập nhật trạng thái đơn
        don.trang_thai = 'thanh_cong'
        don.save()
        # 2. (Tùy chọn) Có thể đánh dấu phòng là "Đã thuê" tại đây nếu muốn
    
    modeladmin.message_user(request, "Đã duyệt các đơn được chọn thành công!")

duyet_don_hang.short_description = "✅ Duyệt đơn đã chọn (Xác nhận cọc)"

class DonDatPhongAdmin(admin.ModelAdmin):
    list_display = ('id', 'nguoi_thue', 'get_ten_phong', 'tien_coc', 'trang_thai', 'ngay_tao', 'nut_xoa_nhanh')
    
    list_editable = ('trang_thai',)
    list_filter = ('trang_thai', 'ngay_tao')
    def get_ten_phong(self, obj):
        return obj.phong.ten
    get_ten_phong.short_description = 'Phòng Đặt'
    def nut_xoa_nhanh(self, obj):
        delete_url = reverse('admin:map_app_dondatphong_delete', args=[obj.id])
        return mark_safe(f'''
            <a href="{delete_url}" style="
                background-color: #dc3545; 
                color: white; 
                padding: 5px 10px; 
                border-radius: 5px; 
                text-decoration: none; 
                font-weight: bold;
                font-size: 12px;">
                <i class="fas fa-trash"></i> Xóa
            </a>
        ''')
    nut_xoa_nhanh.short_description = 'Hành động' 

admin.site.register(DonDatPhong, DonDatPhongAdmin)
admin.site.register(PhongTro, PhongTroAdmin)
admin.site.register(TinTuc, TinTucAdmin)