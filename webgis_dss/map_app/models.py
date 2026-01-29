
# Create your models here.
from django.contrib.gis.db import models # Quan trọng: Phải import từ gis.db

class PhongTro(models.Model):
    # Các thông tin cơ bản
    ten = models.CharField(max_length=200, verbose_name="Tên phòng trọ")
    dia_chi = models.CharField(max_length=500, verbose_name="Địa chỉ")
    gia_thue = models.IntegerField(help_text="VNĐ/tháng", verbose_name="Giá thuê")
    
    # Đây là "trái tim" của WebGIS: Field này lưu trữ tọa độ (Kinh độ/Vĩ độ)
    # srid=4326 là hệ tọa độ GPS chuẩn quốc tế (WGS84)
    location = models.PointField(srid=4326, verbose_name="Vị trí trên bản đồ")
    
    mo_ta = models.TextField(blank=True, verbose_name="Mô tả chi tiết")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ten