from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User
from django.db.models import UniqueConstraint

# 1. BẢNG NHÀ TRỌ
class NhaTro(models.Model):
    ten_nha  = models.CharField(max_length=200, verbose_name="Tên khu nhà trọ")
    dia_chi  = models.CharField(max_length=255)
    location = gis_models.PointField(srid=4326)
    hinh_anh = models.ImageField(upload_to='nha_tro/', blank=True, null=True)
    mo_ta    = models.TextField(null=True, blank=True, verbose_name="Mô tả chung")
    created_at = models.DateTimeField(auto_now_add=True)
    favorites  = models.ManyToManyField(User, related_name='nha_tro_yeu_thich', blank=True)

    def __str__(self):
        return self.ten_nha

# 2. BẢNG PHÒNG TRỌ
class PhongTro(models.Model):
    TRANG_THAI_PHONG = [
        ('trong',  '🟢 Còn trống'),
        ('da_dat', '🔴 Đã đặt'),
    ]
    nha_tro   = models.ForeignKey(NhaTro, on_delete=models.CASCADE, related_name='danh_sach_phong')
    ten_phong = models.CharField(max_length=50, verbose_name="Số phòng (VD: P.101)")
    gia_thue  = models.DecimalField(max_digits=10, decimal_places=0)
    dien_tich = models.FloatField(default=20)
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI_PHONG, default='trong')

    # ✅ FIELD MỚI – chạy makemigrations + migrate sau khi thêm
    hinh_anh  = models.ImageField(upload_to='phong_tro/', blank=True, null=True)

    def __str__(self):
        return f"{self.ten_phong} - {self.nha_tro.ten_nha}"

# 3. HÌNH ẢNH NHÀ TRỌ
class HinhAnhNhaTro(models.Model):
    nha_tro  = models.ForeignKey(NhaTro, on_delete=models.CASCADE, related_name='danh_sach_anh')
    hinh_anh = models.ImageField(upload_to='nhatro_gallery/')

    def __str__(self):
        return f"Ảnh phụ của: {self.nha_tro.ten_nha}"

# 4. TIN TỨC
class TinTuc(models.Model):
    tieu_de  = models.CharField(max_length=200, verbose_name="Tiêu đề")
    hinh_anh = models.ImageField(upload_to='tin_tuc/', blank=True, null=True)
    noi_dung = models.TextField(verbose_name="Nội dung")
    ngay_dang = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tieu_de

class HinhAnhTinTuc(models.Model):
    tin_tuc  = models.ForeignKey(TinTuc, on_delete=models.CASCADE, related_name='danh_sach_anh_tin')
    hinh_anh = models.ImageField(upload_to='tin_tuc_phu/')

# 5. ĐƠN ĐẶT PHÒNG
class DonDatPhong(models.Model):
    TRANG_THAI_CHOICES = [
        ('cho_xac_nhan', '⏳ Chờ xác nhận'),
        ('da_dat_coc',   '✅ Đã đặt cọc'),
        ('huy',          '❌ Đã hủy'),
    ]
    nguoi_thue  = models.ForeignKey(User, on_delete=models.CASCADE)
    phong       = models.ForeignKey(PhongTro, on_delete=models.CASCADE)
    ngay_tao    = models.DateTimeField(auto_now_add=True)
    ngay_don_vao = models.DateField(verbose_name="Ngày dự kiến dọn vào")
    tien_coc    = models.DecimalField(max_digits=10, decimal_places=0)
    trang_thai  = models.CharField(max_length=20, choices=TRANG_THAI_CHOICES, default='cho_xac_nhan')
    ghi_chu     = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nguoi_thue.username} đặt {self.phong.ten_phong}"

# 6. ĐÁNH GIÁ
class DanhGia(models.Model):
    nha_tro        = models.ForeignKey(NhaTro, on_delete=models.CASCADE, related_name='danh_sach_danh_gia')
    nguoi_danh_gia = models.ForeignKey(User, on_delete=models.CASCADE)
    so_sao         = models.IntegerField(default=5)
    noi_dung       = models.TextField()
    ngay_tao       = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [UniqueConstraint(fields=['nha_tro', 'nguoi_danh_gia'], name='unique_review_per_user')]

# 7. KHIẾU NẠI
class KhieuNai(models.Model):
    TRANG_THAI = [
        ('moi',       'Mới tiếp nhận'),
        ('dang_xu_ly','Đang xử lý'),
        ('da_xong',   'Đã giải quyết'),
    ]
    nguoi_gui  = models.ForeignKey(User, on_delete=models.CASCADE)
    tieu_de    = models.CharField(max_length=200)
    noi_dung   = models.TextField()
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI, default='moi')
    ngay_tao   = models.DateTimeField(auto_now_add=True)

# ============================================================
# THÊM VÀO CUỐI models.py
# ============================================================

class TrangGioiThieu(models.Model):
    """
    Singleton model – chỉ có 1 bản ghi duy nhất.
    Admin vào trang quản trị để sửa nội dung, không cần code lại.
    """
    # --- Phần HERO (banner đầu trang) ---
    tieu_de_chinh   = models.CharField(max_length=200, default="Về Chúng Tôi",
                                        verbose_name="Tiêu đề chính")
    mo_ta_ngan      = models.TextField(default="Mô tả ngắn hiển thị dưới tiêu đề.",
                                        verbose_name="Mô tả ngắn (hero)")
    hinh_anh_banner = models.ImageField(upload_to='gioi_thieu/', blank=True, null=True,
                                         verbose_name="Ảnh banner")

    # --- Phần SỨ MỆNH ---
    tieu_de_su_menh = models.CharField(max_length=200, default="Sứ Mệnh Của Chúng Tôi",
                                        verbose_name="Tiêu đề sứ mệnh")
    noi_dung_su_menh = models.TextField(default="Nhập nội dung sứ mệnh tại đây.",
                                         verbose_name="Nội dung sứ mệnh")

    # --- Phần CON SỐ THỐNG KÊ ---
    so_phong        = models.IntegerField(default=0, verbose_name="Số phòng trọ")
    so_sinh_vien    = models.IntegerField(default=0, verbose_name="Sinh viên tin dùng")
    so_quan         = models.IntegerField(default=0, verbose_name="Quận/Huyện phủ sóng")
    so_nam          = models.IntegerField(default=0, verbose_name="Năm hoạt động")

    # --- Phần ĐỘI NGŨ (tên + mô tả, ảnh tuỳ chọn) ---
    thanh_vien_1_ten    = models.CharField(max_length=100, blank=True, verbose_name="Thành viên 1 – Tên")
    thanh_vien_1_chuc_vu = models.CharField(max_length=100, blank=True, verbose_name="Thành viên 1 – Chức vụ")
    thanh_vien_1_anh    = models.ImageField(upload_to='gioi_thieu/doi_ngu/', blank=True, null=True,
                                             verbose_name="Thành viên 1 – Ảnh")

    thanh_vien_2_ten    = models.CharField(max_length=100, blank=True, verbose_name="Thành viên 2 – Tên")
    thanh_vien_2_chuc_vu = models.CharField(max_length=100, blank=True, verbose_name="Thành viên 2 – Chức vụ")
    thanh_vien_2_anh    = models.ImageField(upload_to='gioi_thieu/doi_ngu/', blank=True, null=True,
                                             verbose_name="Thành viên 2 – Ảnh")

    thanh_vien_3_ten    = models.CharField(max_length=100, blank=True, verbose_name="Thành viên 3 – Tên")
    thanh_vien_3_chuc_vu = models.CharField(max_length=100, blank=True, verbose_name="Thành viên 3 – Chức vụ")
    thanh_vien_3_anh    = models.ImageField(upload_to='gioi_thieu/doi_ngu/', blank=True, null=True,
                                             verbose_name="Thành viên 3 – Ảnh")

    # --- Phần LIÊN HỆ ---
    email       = models.EmailField(blank=True, verbose_name="Email liên hệ")
    so_dien_thoai = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    dia_chi     = models.CharField(max_length=255, blank=True, verbose_name="Địa chỉ văn phòng")
    facebook    = models.URLField(blank=True, verbose_name="Link Facebook")
    zalo        = models.CharField(max_length=20, blank=True, verbose_name="Số Zalo")

    class Meta:
        verbose_name = "Trang Giới Thiệu"

    def __str__(self):
        return "Nội dung Trang Giới Thiệu"

    def save(self, *args, **kwargs):
        # Singleton: chỉ cho phép 1 bản ghi
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj