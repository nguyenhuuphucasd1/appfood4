# Kiến trúc hệ thống Vị Việt

## 1. Mục tiêu kiến trúc

Vị Việt là hệ thống mobile-first hỗ trợ khám phá công thức món Việt và nhận
diện món ăn từ ảnh. Kiến trúc hiện tại ưu tiên ba yêu cầu:

1. ứng dụng Flutter chỉ lấy dữ liệu nghiệp vụ từ API, không giữ một catalog
   công thức giả trong mã Dart;
2. backend kiểm soát việc xuất bản công thức, nguồn và giấy phép;
3. model nhận diện 38 nhãn được tách khỏi dataset 30VNFoods dùng cho đánh giá
   và thử nghiệm, tránh ghi đè model production.

## 2. Sơ đồ tổng thể

```text
Người dùng Android / Web
          │
          ▼
Flutter (`mobile/`)
  ├─ screens + widgets
  ├─ AppState (ChangeNotifier)
  ├─ ApiClient / AiService
  ├─ secure token storage
  └─ cache danh mục gần nhất
          │ HTTP/JSON + multipart image
          ▼
FastAPI (`backend/`)
  ├─ auth, users
  ├─ dishes, favorites
  ├─ history, feedback
  ├─ /predict
  └─ /media/dishes
       │              │
       ▼              ▼
SQLite/SQLAlchemy   ViT-L/16 + Transformers
       │              │
       └──── canonical dish mapping ────┘
                       │
                       ▼
          Công thức + nguồn + giấy phép
```

## 3. Ứng dụng Flutter

Mã nguồn Flutter nằm tại `mobile/`. Điểm vào ứng dụng là
`mobile/lib/main.dart`.

- `models/`: ánh xạ JSON API thành model Dart.
- `screens/`: đăng nhập, đăng ký, trang chủ, danh mục, camera AI, kết quả AI,
  chi tiết công thức, yêu thích, lịch sử và hồ sơ.
- `services/`: HTTP JSON, multipart upload, refresh token và cấu hình URL.
- `state/`: trạng thái phiên, danh mục, yêu thích và lịch sử.
- `widgets/`: thành phần UI tái sử dụng, gồm logo, ảnh món và thẻ món.
- `theme/`: màu sắc và typography dùng chung.

`ApiConfig.baseUrl` tự chọn `10.0.2.2:8000` trên Android Emulator và
`127.0.0.1:8000` trên web/desktop. Thiết bị thật phải nhận URL qua
`--dart-define=API_BASE_URL=...`.

## 4. Backend FastAPI

Backend nằm tại `backend/`; `backend/app.py` tạo ứng dụng, mount static media,
đăng ký router, chạy migration và seed catalog nhãn.

- `ai/`: nạp model singleton và suy luận ảnh.
- `routers/`: auth, user, dish, favorite, history và feedback.
- `migrations/`: migration Alembic có version.
- `recipes/`: chuẩn hóa tên/alias và repository công thức.
- `scripts/`: tải model/dataset, audit, tạo split sạch, tải ảnh và import.
- `data/recipes/`: catalog công thức, metadata nguồn và giấy phép.
- `static/dishes/`: 38 ảnh WebP đã audit để API phục vụ qua `/media`.
- `models/`: model production local; thư mục này không đưa lên Git.

## 5. Dữ liệu và tính toàn vẹn

SQLite mặc định ở `backend/data/vi_viet.db`. Quan hệ chính:

```text
users ──< refresh_sessions
users ──< favorites >── dishes
users ──< prediction_history ──< prediction_feedback
dishes ──< recipe_ingredients
dishes ──< recipe_steps
dishes ──< recipe_references
```

Importer cập nhật theo `dish.slug`, không tạo ID mới khi chạy lại. Một món chỉ
được API đánh dấu `hasRecipe=true` khi có đầy đủ nội dung, nguồn, giấy phép,
nguyên liệu, bước làm và metadata ảnh. Với nội dung biên soạn, cần ít nhất hai
nguồn tham khảo; với nội dung dịch từ nguồn mở, cần ít nhất một nguồn phiên bản
cố định.

## 6. Luồng nhận diện AI

1. Flutter lấy ảnh từ camera hoặc thư viện và chỉ giữ preview trong phiên.
2. Client gửi multipart field `image` tới `POST /predict`.
3. Backend kiểm tra MIME, kích thước byte và khả năng giải mã ảnh.
4. processor chính thức của model chuẩn hóa ảnh RGB 384×384.
5. ViT trả xác suất; backend giữ Top 3 cho lịch sử và đánh giá.
6. nhãn Top 1 được chuẩn hóa rồi ánh xạ sang bản ghi `dishes`.
7. response trả `prediction`, `top3`, `recognizedDish` và `recipe`.
8. Flutter chỉ hiển thị Top 1 và mở trực tiếp trang công thức của
   `recognizedDish`.

Ảnh upload không được ghi vào database hay ổ đĩa; lịch sử ghi
`imageStored=false`.

## 7. Xác thực và bảo mật

- mật khẩu được băm bằng Argon2 qua `pwdlib`;
- access token và refresh token là JWT HS256;
- refresh token có phiên trong database, được xoay vòng khi refresh và thu hồi
  khi logout;
- Flutter lưu token trong `flutter_secure_storage`;
- rate limit hiện áp dụng theo IP trong bộ nhớ của một tiến trình;
- production bắt buộc cấu hình `AUTH_SECRET_KEY` tối thiểu 32 byte;
- `.kaggle`, database, model, dataset, cache và artifact cục bộ bị loại khỏi
  Git.

## 8. Quyết định ổn định đường dẫn

Các đường dẫn runtime sau là giao diện nội bộ ổn định của workspace và không
được di chuyển nếu chưa sửa đồng bộ code, script và tài liệu:

- `backend/models/vietnamese_food_classifier/`
- `backend/data/vi_viet.db`
- `backend/data/recipes/`
- `backend/static/dishes/`
- `datasets/raw/`
- `datasets/processed/`
- `artifacts/backups/`
- `mobile/lib/main.dart`

## 9. Hạn chế triển khai hiện tại

SQLite phù hợp đồ án và chạy đơn máy nhưng không phải lựa chọn cho nhiều API
instance ghi đồng thời. Rate limiter chưa dùng kho dùng chung. Model ViT-L/16
lớn và suy luận CPU có thể chậm; triển khai production nên cân nhắc GPU, model
nhẹ hơn, PostgreSQL và reverse proxy.
