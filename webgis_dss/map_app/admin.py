from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from django.utils.html import mark_safe
from django.urls import reverse

# 1. Lọc lại Import: Chỉ lấy đúng các Model từ file models.py mới
from .models import NhaTro, PhongTro, HinhAnhNhaTro, TinTuc, HinhAnhTinTuc, DonDatPhong, DanhGia, KhieuNai

# --- HÀM HỖ TRỢ HIỂN THỊ ẢNH ---
def get_hinh_anh_preview(obj):
    if obj.hinh_anh:
        return mark_safe(f'<img src="{obj.hinh_anh.url}" style="width: 80px; height:auto; border-radius: 5px; border: 1px solid #ddd;" />')
    return mark_safe('<span style="color: #999;">(Chưa có ảnh)</span>')

# --- QUẢN LÝ NHÀ TRỌ (GẮN BẢN ĐỒ) ---
class NhaTroAdmin(LeafletGeoAdmin):
    # Sửa 'ten' thành 'ten_nha', bỏ 'gia_thue' vì giá đã chuyển sang bảng Phòng
    list_display = ('ten_nha', 'hinh_anh_preview', 'dia_chi', 'created_at')
    search_fields = ('ten_nha', 'dia_chi')
    readonly_fields = ('hinh_anh_preview',)
    
    settings_overrides = {
       'DEFAULT_CENTER': (10.7769, 106.7009),
       'DEFAULT_ZOOM': 13,
    }

    def hinh_anh_preview(self, obj):
        return get_hinh_anh_preview(obj)
    hinh_anh_preview.short_description = "Ảnh nhà trọ"

# --- QUẢN LÝ CHI TIẾT TỪNG PHÒNG TRỌ ---
class PhongTroAdmin(admin.ModelAdmin):
    list_display = ('ten_phong', 'nha_tro', 'gia_thue', 'dien_tich', 'trang_thai')
    list_filter = ('trang_thai', 'nha_tro')
    search_fields = ('ten_phong', 'nha_tro__ten_nha')
    # Cho phép sửa nhanh giá và trạng thái ngay ngoài danh sách
    list_editable = ('trang_thai', 'gia_thue')

# --- QUẢN LÝ TIN TỨC ---
class TinTucAdmin(admin.ModelAdmin):
    list_display = ('tieu_de', 'hinh_anh_preview', 'ngay_dang')
    search_fields = ('tieu_de',)
    list_filter = ('ngay_dang',)
    readonly_fields = ('hinh_anh_preview',) 
    fields = ('tieu_de', 'hinh_anh_preview', 'hinh_anh', 'noi_dung')

    def hinh_anh_preview(self, obj):
        return get_hinh_anh_preview(obj)
    hinh_anh_preview.short_description = "Ảnh đại diện"

# --- HÀM DUYỆT ĐƠN HÀNG NHANH ---
def duyet_don_hang(modeladmin, request, queryset):
    for don in queryset:
        # Sửa 'thanh_cong' thành 'da_dat_coc' để khớp với TRANG_THAI_CHOICES trong models.py
        don.trang_thai = 'da_dat_coc'
        don.save()
    modeladmin.message_user(request, "Đã duyệt các đơn được chọn thành công!")

duyet_don_hang.short_description = "✅ Duyệt đơn đã chọn (Xác nhận cọc)"

# --- QUẢN LÝ ĐƠN ĐẶT PHÒNG ---
class DonDatPhongAdmin(admin.ModelAdmin):
    list_display = ('id', 'nguoi_thue', 'get_ten_phong', 'tien_coc', 'trang_thai', 'ngay_tao', 'nut_xoa_nhanh')
    list_editable = ('trang_thai',)
    list_filter = ('trang_thai', 'ngay_tao')
    actions = [duyet_don_hang] # Tích hợp nút duyệt đơn vào hệ thống
    
    def get_ten_phong(self, obj):
        # Cập nhật cách gọi tên phòng (kèm tên nhà để dễ phân biệt)
        return f"{obj.phong.ten_phong} ({obj.phong.nha_tro.ten_nha})"
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

# --- ĐĂNG KÝ VÀO GIAO DIỆN ADMIN ---
admin.site.register(NhaTro, NhaTroAdmin)
admin.site.register(PhongTro, PhongTroAdmin)
admin.site.register(TinTuc, TinTucAdmin)
admin.site.register(DonDatPhong, DonDatPhongAdmin)

# Đăng ký các bảng phụ
admin.site.register(HinhAnhNhaTro)
admin.site.register(HinhAnhTinTuc)
admin.site.register(DanhGia)
admin.site.register(KhieuNai)