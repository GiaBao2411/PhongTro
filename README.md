🏠 <span style="color:#2ecc71">HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY DỰ ÁN WEBGIS: SMARTRENT</span>

Hệ thống
<span style="color:#3498db"><b>WebGIS Quản lý và Tìm kiếm nhà trọ (SmartRent)</b></span>
được xây dựng bằng:


<span style="color:#f39c12"><b>Django Framework</b></span>
<span style="color:#f39c12"><b>PostgreSQL</b></span>
<span style="color:#f39c12"><b>PostGIS</b></span>

📌 <span style="color:#e74c3c">BƯỚC 1: TẠO CƠ SỞ DỮ LIỆU</span>

Nhóm đã chuẩn bị sẵn file:
<span style="color:#9b59b6"><b>webgis_db.sql / .backup</b></span>

👉 Thực hiện:

Mở pgAdmin 4

Tạo database:
webgis_db

Chạy lệnh:
CREATE EXTENSION IF NOT EXISTS postgis;

Chuột phải database → <span style="color:#2980b9"><b>Restore...</b></span>
Chọn file SQL
Nhấn <span style="color:#27ae60"><b>Restore</b></span>


📌 <span style="color:#e67e22">BƯỚC 2: CÀI MÔI TRƯỜNG & GDAL</span>

<span style="color:red"><b>BẮT BUỘC dùng Anaconda / Miniconda</b></span>

conda create -n webgis_env python=3.9

conda activate webgis_env

conda install -c conda-forge gdal


📌 <span style="color:#1abc9c">BƯỚC 3: CẤU HÌNH PROJECT</span>

👉 Mở project

cd <duong_dan_project>
code .

👉 Cài thư viện

pip install -r requirements.txt

⚠️ <span style="color:red">BƯỚC QUAN TRỌNG NHẤT</span>

Mở file:
webgis_dss/settings.py

🔧 Sửa GDAL:

import os
if os.name == 'nt':
    VENV_BASE = r"C:\Users\Tên_Máy_Tính\anaconda3\envs\webgis_env"

    os.environ['PATH'] = os.path.join(VENV_BASE, 'Library', 'bin') + ';' + os.environ['PATH']
    GDAL_LIBRARY_PATH = os.path.join(VENV_BASE, 'Library', 'bin', 'gdal.dll')

    os.environ['GDAL_DATA'] = os.path.join(VENV_BASE, 'Library', 'share', 'gdal')
    os.environ['PROJ_LIB'] = os.path.join(VENV_BASE, 'Library', 'share', 'proj')
🔧 DATABASE

Nếu mật khẩu PostgreSQL khác:

- PASSWORD: 123
+ PASSWORD: <mat_khau_cua_ban>
📌 <span style="color:#8e44ad">

BƯỚC 4: CHẠY SERVER</span>

<span style="color:orange"><b>Không cần migrate</b></span>

python manage.py runserver

🌐 <span style="color:#16a085">TRUY CẬP</span>
http://127.0.0.1:8000/
