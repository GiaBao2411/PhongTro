from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User

class PhongTro(models.Model):
    ten = models.CharField(max_length=200)
    gia_thue = models.DecimalField(max_digits=10, decimal_places=0)
    dien_tich = models.FloatField(default=20)
    dia_chi = models.CharField(max_length=255)
    location = gis_models.PointField(srid=4326) 
    hinh_anh = models.ImageField(upload_to='phong_tro/', blank=True, null=True)
    mo_ta = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Trường lưu danh sách người thích
    favorites = models.ManyToManyField(User, related_name='favorite_rooms', blank=True)

    def __str__(self):
        return self.ten

class TinTuc(models.Model):
    tieu_de = models.CharField(max_length=200)
    noi_dung = models.TextField()
    ngay_dang = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.tieu_de