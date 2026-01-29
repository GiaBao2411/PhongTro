from django.contrib.gis.db import models

class PhongTro(models.Model):
    ten = models.CharField(max_length=200, verbose_name="Tiêu đề tin đăng")
    dia_chi = models.CharField(max_length=500, verbose_name="Địa chỉ cụ thể")
    gia_thue = models.IntegerField(verbose_name="Giá (VNĐ/tháng)")
    
    # Các trường mới thêm vào
    dien_tich = models.IntegerField(default=20, verbose_name="Diện tích (m2)")
    sdt_lien_he = models.CharField(max_length=15, default="0909000000", verbose_name="SĐT Liên hệ")
    hinh_anh = models.ImageField(upload_to='phong_tro/', blank=True, null=True, verbose_name="Hình ảnh thực tế")
    
    # Trường quan trọng nhất: Tọa độ
    location = models.PointField(srid=4326, verbose_name="Vị trí bản đồ")
    
    mo_ta = models.TextField(blank=True, verbose_name="Mô tả chi tiết")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ten