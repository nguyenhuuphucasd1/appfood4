# Vị Việt Mobile

Ứng dụng Flutter cho Android, iOS và web, kết nối với FastAPI ở thư mục `backend/`. Giao diện dùng phong cách kem–xanh–cam; màn hình hẹp dùng thanh điều hướng dưới, còn màn hình từ 900 px dùng `NavigationRail` và giới hạn chiều rộng nội dung.

## Chức năng MVP

- Khách có thể duyệt danh mục 38 món, tìm kiếm/lọc, xem trạng thái công thức và nhận diện ảnh từ camera hoặc thư viện.
- Tài khoản thật hỗ trợ đăng ký, đăng nhập, khôi phục phiên, tự refresh token, logout và cập nhật hồ sơ.
- Danh mục lấy từ `GET /dishes`, không dùng nhãn Dart tĩnh làm nguồn dữ liệu giao diện; lần tải thành công gần nhất được cache bằng `SharedPreferences`.
- Yêu thích cập nhật lạc quan rồi rollback khi API thất bại và được đồng bộ theo tài khoản.
- Người đã đăng nhập có lịch sử nhận diện và có thể gửi nhãn xác nhận/sửa cho một `predictionId`.
- Ảnh nhận diện chỉ được giữ trong bộ nhớ để preview ở phiên hiện tại; backend lưu `imageStored: false`.
- Toàn bộ 38 món hiện có ảnh và công thức kèm nguồn; placeholder vẫn được giữ làm phương án an toàn khi ảnh tải lỗi hoặc backend trả dữ liệu không hợp lệ.
- Các màn lấy dữ liệu có trạng thái loading, rỗng, lỗi mạng và thử lại.

Tại thời điểm cập nhật tài liệu, backend có **38 công thức kèm nguồn và 38 ảnh có metadata giấy phép**.

## Kiến trúc Flutter

```text
screens/widgets
      │
      ▼
AppState (ChangeNotifier + InheritedNotifier)
  ├─ user/session
  ├─ dishes + cache
  ├─ favorites
  └─ prediction history
      │
      ▼
ApiClient / AiService
  ├─ JSON requests
  ├─ multipart /predict
  ├─ Bearer access token
  └─ refresh rồi retry một lần khi nhận 401
      │
      ▼
FastAPI
```

Access/refresh token được lưu bằng `flutter_secure_storage`. Nếu secure storage không khả dụng, phiên trong bộ nhớ vẫn dùng được đến khi ứng dụng đóng. Danh mục cache không chứa công thức chi tiết và chỉ dùng làm dữ liệu gần nhất khi request danh mục cơ bản thất bại.

## Chuẩn bị

1. Từ thư mục gốc project, cài và chạy backend:

   ```bat
   setup_backend.bat
   .venv\Scripts\python -m backend.migrations.runner
   run_backend.bat
   ```

2. Trong một terminal khác:

   ```bat
   cd mobile
   flutter pub get
   flutter doctor -v
   ```

Backend phải tiếp tục chạy trong lúc ứng dụng dùng API hoặc nhận diện AI.

## Cấu hình API

Ứng dụng nhận URL lúc build/run qua `API_BASE_URL`:

```bat
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
```

Nếu không truyền, ứng dụng tự chọn:

| Nền tảng | URL mặc định |
| --- | --- |
| Android Emulator | `http://10.0.2.2:8000` |
| Flutter Web | `http://127.0.0.1:8000` |
| Windows/iOS simulator | `http://127.0.0.1:8000` |

Thiết bị Android/iOS thật phải dùng IP LAN của máy chạy backend, không dùng `127.0.0.1`. Đảm bảo hai thiết bị cùng mạng và firewall cho phép cổng 8000.

## Chạy theo nền tảng

Android Emulator:

```bat
flutter run -d emulator-5554
```

Web ở cổng đã có trong CORS mặc định của backend:

```bat
flutter run -d chrome --web-port=8080 --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

Nếu dùng cổng hoặc hostname khác, thêm origin đầy đủ vào biến `CORS_ORIGINS` trước khi khởi động backend. Ví dụ PowerShell:

```powershell
$env:CORS_ORIGINS = "http://localhost:8080,http://127.0.0.1:8080"
```

Build:

```bat
flutter build apk --debug
flutter build web --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

APK debug nằm tại `build/app/outputs/flutter-apk/app-debug.apk`.

## Luồng sử dụng

1. Chọn **Tiếp tục với tư cách khách** để duyệt món và dùng AI, hoặc đăng ký tài khoản bằng tên, email và mật khẩu tối thiểu 8 ký tự.
2. Ở danh mục, tìm theo tên không dấu/có dấu và dùng bộ lọc vùng miền, danh mục, thời gian hoặc độ khó.
3. Ở tab Máy ảnh, chọn camera/thư viện, xem preview rồi gửi ảnh tới `POST /predict`.
4. Màn kết quả chỉ hiển thị dự đoán Top 1. Nhấn **Xem công thức** để mở đúng món; nếu kết quả sai, dùng **Kết quả chưa đúng?** để tìm trong 38 món và gửi feedback.
5. Dùng biểu tượng trái tim để đồng bộ món yêu thích. Khách sẽ được yêu cầu đăng nhập trước khi lưu.
6. Mở chi tiết món để xem dữ liệu API; nếu `hasRecipe` là `false`, ứng dụng chỉ hiển thị thông báo thiếu nguồn.

Ảnh hỗ trợ là JPEG/JPG/PNG, tối đa 10 MB ở backend. Client có timeout 20 giây cho JSON và 90 giây cho nhận diện.

## Kiểm tra

```bat
flutter analyze
flutter test
flutter test test/golden_test.dart
flutter build apk --debug
flutter build web
```

Golden test bao phủ cả viewport mobile và desktop. Khi thay đổi giao diện có chủ đích, hãy kiểm tra ảnh thực tế ở cả hai kích thước trước khi cập nhật baseline.

## Xử lý lỗi thường gặp

- **Android Emulator không gọi được backend:** dùng `10.0.2.2`, không dùng `127.0.0.1`.
- **Web báo CORS:** chạy web ở cổng 8080 hoặc thêm origin của Flutter dev server vào `CORS_ORIGINS`, rồi khởi động lại backend.
- **Thiết bị thật không kết nối:** dùng IP LAN của máy host, kiểm tra cùng Wi-Fi và firewall cổng 8000.
- **Backend trả 503 ở lần đầu:** kiểm tra model đã được tải bởi `setup_backend.bat`; model khoảng 1,21 GB.
- **Ảnh bị từ chối:** chỉ dùng JPEG/JPG/PNG hợp lệ và nhỏ hơn giới hạn backend.
- **Phiên hết hạn:** client tự refresh và retry một lần. Nếu refresh token cũng không hợp lệ, dữ liệu phiên được xóa và người dùng cần đăng nhập lại.

Xem `../README.md` để biết toàn bộ API, migration, biến môi trường và cách nhập công thức có nguồn.
