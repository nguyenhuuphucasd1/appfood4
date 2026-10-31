# Cài đặt và chạy Vị Việt trên Windows

## 1. Yêu cầu

- Windows 10/11 64-bit;
- Python tương thích với PyTorch trong `backend/requirements.txt`;
- Flutter SDK và Dart phù hợp `mobile/pubspec.yaml`;
- Android Studio có Flutter/Dart plugin;
- Android SDK, platform tools và một Android Virtual Device;
- đủ dung lượng ổ D cho model, dataset, cache và build.

Kiểm tra nhanh:

```bat
python --version
flutter --version
flutter doctor -v
adb --version
```

## 2. Cài backend lần đầu

Mở terminal tại `D:\appfood4`:

```bat
setup_backend.bat
```

Script tạo `.venv`, cài dependency, chạy migration và tải model vào
`backend/models/vietnamese_food_classifier/`. Cache pip/Hugging Face/Torch và
thư mục tạm đều được trỏ về workspace trên ổ D.

Cài thủ công khi cần:

```bat
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt
.venv\Scripts\python -m backend.migrations.runner
.venv\Scripts\python backend\scripts\download_model.py
```

## 3. Chạy backend

```bat
run_backend.bat
```

Giữ cửa sổ này mở. Kiểm tra:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

Để khởi động nhẹ mà không nạp model ngay:

```powershell
$env:MODEL_LOAD_ON_STARTUP = "false"
.\run_backend.bat
```

## 4. Chạy bằng Android Studio và Shift+F10

1. mở đúng thư mục root `D:\appfood4`, không mở thư mục Git lồng cũ;
2. bảo đảm Flutter và Dart plugin đã bật;
3. mở Device Manager và khởi động một Android Emulator;
4. chờ thiết bị xuất hiện trong device selector;
5. chọn run configuration **Vị Việt - Flutter** từ `.run/`;
6. nhấn `Shift+F10` hoặc nút Run.

Cấu hình dùng chung trỏ đến `mobile/lib/main.dart`. Backend vẫn chạy riêng qua
`run_backend.bat`; không gắn server Python vào Gradle.

Nếu Android Studio chưa nhận cấu hình, mở `mobile/lib/main.dart`, nhấp phải
chọn **Run 'main.dart'** một lần, sau đó chọn lại **Vị Việt - Flutter**.

## 5. Chạy Flutter bằng terminal

```bat
cd mobile
flutter pub get
flutter run
```

Android Emulator dùng URL mặc định `http://10.0.2.2:8000`. Thiết bị thật cần IP
LAN của máy backend:

```bat
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
```

Web:

```bat
flutter run -d chrome --web-port=8080 --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

## 6. Biến môi trường backend

| Biến | Mặc định | Vai trò |
| --- | --- | --- |
| `DATABASE_URL` | SQLite `backend/data/vi_viet.db` | Kết nối database |
| `APP_ENV` | `development` | Bật kiểm tra production |
| `AUTH_SECRET_KEY` | ngẫu nhiên mỗi tiến trình dev | Khóa JWT |
| `ACCESS_TOKEN_MINUTES` | `30` | Tuổi access token |
| `REFRESH_TOKEN_DAYS` | `30` | Tuổi refresh token |
| `CORS_ORIGINS` | localhost/127.0.0.1 cổng 3000, 8080 | Origin web |
| `MODEL_LOAD_ON_STARTUP` | `true` | Nạp model lúc start |
| `CONFIDENCE_THRESHOLD` | `0.60` | Ngưỡng accepted |
| `TOP_K` | `3` | Số dự đoán backend giữ |
| `MAX_IMAGE_BYTES` | `10485760` | Giới hạn upload |
| `MAX_IMAGE_PIXELS` | `40000000` | Giới hạn pixel |
| `AUTH_RATE_LIMIT_PER_MINUTE` | `60` | Rate limit auth |
| `PREDICT_RATE_LIMIT_PER_MINUTE` | `30` | Rate limit AI |

## 7. Migration, test và build

```bat
.venv\Scripts\python -m backend.migrations.runner
.venv\Scripts\python -m unittest discover -s backend\tests -p "test_*.py" -v
.venv\Scripts\python -m backend.scripts.audit_recipe_data

cd mobile
flutter analyze
flutter test
flutter build apk --debug
```

APK ở `mobile/build/app/outputs/flutter-apk/app-debug.apk`.

## 8. Lỗi thường gặp

- **Emulator không gọi được API:** dùng `10.0.2.2`, không dùng `127.0.0.1`.
- **Backend không start:** kiểm tra `.venv`, migration, cổng 8000 và model local.
- **503 model unavailable:** chạy lại `backend/scripts/download_model.py` và
  kiểm tra dung lượng ổ D.
- **Web bị CORS:** thêm origin chính xác vào `CORS_ORIGINS`, rồi restart API.
- **Thiết bị thật không kết nối:** cùng Wi-Fi, dùng IP LAN và cho phép firewall.
- **Ảnh bị 413/415/422:** giảm kích thước, dùng JPEG/PNG hợp lệ.
- **Shift+F10 không có cấu hình:** mở root project, bật Flutter plugin và chọn
  **Vị Việt - Flutter**.
- **Gradle tải nhầm ổ:** cấu hình `GRADLE_USER_HOME` trên ổ D trước khi build
  nếu máy có giới hạn ổ C.
