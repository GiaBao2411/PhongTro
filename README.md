# 🏠 SmartRent – Hệ Thống Tìm Phòng Trọ Thông Minh (WebGIS)

> Nền tảng tìm kiếm phòng trọ dựa trên công nghệ GIS, hỗ trợ tìm kiếm theo thời gian di chuyển thực tế.  
> Xây dựng bằng **Django 4.2 + PostgreSQL/PostGIS + Leaflet.js**

---

## 📋 Mục lục

1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Cài đặt môi trường](#2-cài-đặt-môi-trường)
3. [Cài đặt PostgreSQL & PostGIS](#3-cài-đặt-postgresql--postgis)
4. [Tải & cấu hình dự án](#4-tải--cấu-hình-dự-án)
5. [Cấu hình database](#5-cấu-hình-database)
6. [Chạy dự án](#6-chạy-dự-án)
7. [Tạo tài khoản Admin](#7-tạo-tài-khoản-admin)
8. [Cấu trúc thư mục](#8-cấu-trúc-thư-mục)
9. [Tính năng hệ thống](#9-tính-năng-hệ-thống)
10. [Phân quyền người dùng](#10-phân-quyền-người-dùng)
11. [Lỗi thường gặp](#11-lỗi-thường-gặp)

---

## 1. Yêu cầu hệ thống

| Phần mềm | Phiên bản khuyến nghị | Ghi chú |
|---|---|---|
| Windows | 10 / 11 | Đã test trên Windows |
| Anaconda | Mới nhất | Quản lý môi trường Python |
| Python | 3.10+ | Cài qua Anaconda |
| PostgreSQL | 14 / 15 / 16 | Database chính |
| PostGIS | 3.x | Extension GIS cho PostgreSQL |
| VS Code | Mới nhất | IDE khuyến nghị |
| Git | Mới nhất | Clone source code |

---

## 2. Cài đặt môi trường

### Bước 2.1 – Cài Anaconda
1. Tải Anaconda tại: https://www.anaconda.com/download
2. Cài đặt theo hướng dẫn, **tick chọn "Add Anaconda to PATH"**
3. Mở **Anaconda Prompt** (tìm trong Start Menu)

### Bước 2.2 – Tạo môi trường ảo

Mở **Anaconda Prompt** và chạy lần lượt:

```bash
# Tạo môi trường tên webgis_env với Python 3.10
conda create -n webgis_env python=3.10 -y

# Kích hoạt môi trường
conda activate webgis_env
```

> ⚠️ **Quan trọng:** Mọi lệnh tiếp theo đều phải chạy trong môi trường `webgis_env` đã kích hoạt.

### Bước 2.3 – Cài thư viện GDAL & GEOS (bắt buộc cho GIS)

```bash
# Cài GDAL qua conda (bắt buộc, không dùng pip cho bước này)
conda install -c conda-forge gdal -y

# Kiểm tra cài thành công
python -c "from osgeo import gdal; print('GDAL OK:', gdal.__version__)"
```

### Bước 2.4 – Cài các thư viện Python

```bash
pip install django==4.2.23
pip install djangorestframework
pip install django-leaflet
pip install jazzmin
pip install psycopg2-binary
pip install Pillow
pip install requests
```

---

## 3. Cài đặt PostgreSQL & PostGIS

### Bước 3.1 – Tải PostgreSQL

1. Vào https://www.postgresql.org/download/windows/
2. Chọn **PostgreSQL 15** (hoặc 14/16)
3. Tải về file `.exe` và chạy cài đặt
4. Trong quá trình cài:
   - **Password**: đặt `123` (hoặc tùy ý, nhớ cập nhật `settings.py`)
   - **Port**: để mặc định `5432`
   - **Locale**: để mặc định
5. ✅ Tick chọn **Stack Builder** ở cuối quá trình cài

### Bước 3.2 – Cài PostGIS qua Stack Builder

Sau khi PostgreSQL cài xong, Stack Builder sẽ tự mở:
1. Chọn server PostgreSQL vừa cài → **Next**
2. Mở mục **Spatial Extensions** → tick chọn **PostGIS**
3. Nhấn **Next** và chờ tải + cài xong

> Nếu Stack Builder không tự mở: Tìm trong Start Menu → **Stack Builder**

### Bước 3.3 – Tạo database

Mở **pgAdmin 4** (cài kèm PostgreSQL):

1. Đăng nhập bằng password đã đặt lúc cài
2. Click chuột phải vào **Databases** → **Create** → **Database**
3. Đặt tên: `webgis_db` → **Save**

Hoặc dùng **SQL Shell (psql)**:

```sql
-- Mở SQL Shell, đăng nhập xong chạy:
CREATE DATABASE webgis_db;

-- Kết nối vào database vừa tạo
\c webgis_db

-- Kích hoạt extension PostGIS
CREATE EXTENSION postgis;

-- Kiểm tra
SELECT PostGIS_Version();
```

---

## 4. Tải & cấu hình dự án

### Bước 4.1 – Clone source code

Mở **Anaconda Prompt**, điều hướng đến thư mục bạn muốn lưu project:

```bash
cd D:\
git clone https://github.com/<username>/smartrent.git
cd smartrent
```

> Hoặc nếu có file `.zip`: Giải nén vào thư mục, ví dụ `D:\PhongTro\webgis_dss\`

### Bước 4.2 – Mở dự án trong VS Code

```bash
# Trong Anaconda Prompt, điều hướng vào thư mục dự án
cd D:\PhongTro\webgis_dss

# Kích hoạt môi trường
conda activate webgis_env

# Mở VS Code
code .
```

Trong VS Code:
- Nhấn `Ctrl + Shift + P` → gõ **"Python: Select Interpreter"**
- Chọn `webgis_env` (có chữ `conda`)

### Bước 4.3 – Cấu hình `settings.py`

Mở file `webgis_dss/settings.py`, kiểm tra và chỉnh các phần sau:

```python
# ① Đường dẫn GDAL – điều chỉnh theo tên user Windows của bạn
VENV_BASE = r"C:\Users\<TÊN_USER_CỦA_BẠN>\anaconda3\envs\webgis_env"
# Ví dụ: r"C:\Users\Nguyen\anaconda3\envs\webgis_env"

# ② Database – đổi PASSWORD nếu bạn đặt khác
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'webgis_db',
        'USER': 'postgres',
        'PASSWORD': '123',       # ← đổi thành password PostgreSQL của bạn
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

> 💡 **Tìm tên user Windows:** Mở Command Prompt → gõ `echo %USERNAME%`

---

## 5. Cấu hình database

Trong **Anaconda Prompt** (đã `conda activate webgis_env`), điều hướng vào thư mục project:

```bash
cd D:\PhongTro\webgis_dss
```

### Bước 5.1 – Tạo bảng từ models

```bash
python manage.py makemigrations
python manage.py migrate
```

Kết quả mong đợi:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, map_app, sessions
Running migrations:
  Applying map_app.0001_initial... OK
  ...
```

### Bước 5.2 – (Tuỳ chọn) Load dữ liệu mẫu

Nếu dự án có file dữ liệu mẫu:

```bash
python manage.py loaddata data_sample.json
```

---

## 6. Chạy dự án

```bash
# Đảm bảo đang trong thư mục dự án và môi trường đã kích hoạt
conda activate webgis_env
cd D:\PhongTro\webgis_dss

# Chạy server
python manage.py runserver
```

Mở trình duyệt và truy cập:

| Địa chỉ | Mô tả |
|---|---|
| http://127.0.0.1:8000/ | Trang chủ người dùng |
| http://127.0.0.1:8000/he-thong/ | Trang quản trị Admin |
| http://127.0.0.1:8000/chu-tro/ | Trang quản lý Chủ trọ |
| http://127.0.0.1:8000/admin/ | Django Admin mặc định |

---

## 7. Tạo tài khoản Admin

```bash
python manage.py createsuperuser
```

Nhập theo hướng dẫn:
```
Username: admin
Email: admin@gmail.com
Password: (nhập mật khẩu, tối thiểu 8 ký tự)
Password (again): (nhập lại)
```

Sau đó đăng nhập tại http://127.0.0.1:8000/dang-nhap/ bằng tài khoản vừa tạo.

---

## 8. Cấu trúc thư mục

```
webgis_dss/
├── manage.py                   # Lệnh quản lý Django
├── webgis_dss/
│   ├── settings.py             # Cấu hình dự án
│   ├── urls.py                 # URL routing chính
│   └── wsgi.py
├── map_app/
│   ├── models.py               # Định nghĩa database
│   ├── views.py                # Xử lý logic
│   ├── forms.py                # Form đăng ký, cập nhật
│   └── migrations/             # Lịch sử thay đổi database
├── templates/
│   └── map_app/
│       ├── base.html           # Template gốc người dùng
│       ├── home.html
│       ├── map.html
│       ├── detail.html
│       ├── admin_custom/       # Giao diện admin tùy chỉnh
│       │   ├── admin_base.html
│       │   ├── phongtro_form.html
│       │   └── ...
│       └── chu_tro/            # Giao diện chủ trọ
│           ├── base.html
│           ├── dashboard.html
│           └── ...
├── static/
│   └── images/
│       └── banner.jpg          # Ảnh banner trang chủ
└── media/                      # Ảnh upload (tự tạo khi chạy)
```

---

## 9. Tính năng hệ thống

### 👤 Người dùng thường
- Tìm phòng trọ theo **thời gian di chuyển** (isochrone GIS)
- Xem bản đồ, chi tiết khu trọ và từng phòng
- Đặt phòng, thanh toán cọc qua QR VietQR
- Lưu phòng yêu thích, xem lịch sử đặt phòng
- Đánh giá khu trọ, gửi khiếu nại

### 🏠 Chủ trọ (được Admin cấp quyền)
- Quản lý khu trọ và phòng con của mình
- Xem và duyệt đơn đặt phòng từ khách
- Không có quyền truy cập quản lý Users, Tin tức, Khiếu nại

### 👑 Admin (superuser)
- Toàn quyền hệ thống
- Cấp / thu hồi quyền Chủ trọ
- Quản lý tất cả khu trọ, đơn đặt phòng, khiếu nại, tin tức
- Chỉnh sửa nội dung trang Giới thiệu

---

## 10. Phân quyền người dùng

| Chức năng | User thường | Chủ trọ | Admin |
|---|:---:|:---:|:---:|
| Xem / tìm phòng | ✅ | ✅ | ✅ |
| Đặt phòng | ✅ | ✅ | ✅ |
| Quản lý khu trọ của mình | ❌ | ✅ | ✅ |
| Xem đơn đặt phòng của mình | ❌ | ✅ | ✅ |
| Quản lý tất cả khu trọ | ❌ | ❌ | ✅ |
| Quản lý Users | ❌ | ❌ | ✅ |
| Quản lý Tin tức | ❌ | ❌ | ✅ |
| Quản lý Khiếu nại | ❌ | ❌ | ✅ |
| Sửa Trang Giới thiệu | ❌ | ❌ | ✅ |

### Cách cấp quyền Chủ trọ

1. Admin đăng nhập → vào **Quản lý > Users**
2. Tìm tài khoản muốn cấp quyền → nhấn nút **🛡️ Cấp quyền Chủ trọ**
3. Điền số điện thoại, địa chỉ → **Xác nhận**
4. Người dùng đó đăng nhập lại sẽ thấy menu **"Quản lý phòng trọ"** trong dropdown

---

## 11. Lỗi thường gặp

### ❌ `GDAL_LIBRARY_PATH` không tìm thấy

```
ImproperlyConfigured: Could not find the GDAL library
```

**Cách sửa:** Mở `settings.py`, kiểm tra đường dẫn:
```python
VENV_BASE = r"C:\Users\<TÊN_USER_CỦA_BẠN>\anaconda3\envs\webgis_env"
```
Đảm bảo thư mục này tồn tại và file `gdal.dll` có trong `Library\bin\`.

---

### ❌ Không kết nối được PostgreSQL

```
django.db.utils.OperationalError: could not connect to server
```

**Cách sửa:**
1. Kiểm tra PostgreSQL đang chạy: Mở **Services** (Win + R → `services.msc`) → tìm `postgresql` → Start
2. Kiểm tra đúng `PASSWORD` trong `settings.py`
3. Kiểm tra database `webgis_db` đã tồn tại trong pgAdmin

---

### ❌ PostGIS chưa được kích hoạt

```
django.db.utils.ProgrammingError: type "geometry" does not exist
```

**Cách sửa:** Mở pgAdmin → chọn database `webgis_db` → mở **Query Tool** → chạy:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

---

### ❌ Lỗi migrate `relation already exists`

```bash
# Reset migration
python manage.py migrate --fake-initial
```

---

### ❌ Ảnh không hiển thị

Kiểm tra `settings.py` có đầy đủ:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

Và `urls.py` có:
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [...] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

### ❌ `TemplateDoesNotExist`

Kiểm tra thư mục `templates/` nằm đúng trong thư mục gốc project (cùng cấp với `manage.py`).  
Kiểm tra `settings.py`:
```python
TEMPLATES = [{
    ...
    "APP_DIRS": True,   # phải là True
    ...
}]
```

---

## Đây là tất cả các bước để hướng dẫn cho mọi người chạy được web trên máy của mình
