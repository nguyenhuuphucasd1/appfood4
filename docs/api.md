# API Vị Việt

Base URL khi chạy local: `http://127.0.0.1:8000`.

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`
- media ảnh món: `/media/dishes/<ten-file>.webp`
- request/response JSON dùng UTF-8 và tên field dạng camelCase ở biên API.

## Xác thực

Endpoint cá nhân nhận header:

```http
Authorization: Bearer <accessToken>
```

`POST /auth/register` và `POST /auth/login` trả access token, refresh token và
thông tin user. `POST /auth/refresh` xoay vòng cả hai token; client không nên
tái sử dụng refresh token cũ sau khi refresh thành công.

## Danh sách endpoint

| Method | Endpoint | Xác thực | Mục đích |
| --- | --- | --- | --- |
| `GET` | `/health` | Không | Kiểm tra API sẵn sàng |
| `POST` | `/auth/register` | Không | Tạo tài khoản |
| `POST` | `/auth/login` | Không | Đăng nhập |
| `POST` | `/auth/refresh` | Refresh token trong body | Xoay vòng phiên |
| `POST` | `/auth/logout` | Refresh token trong body | Thu hồi phiên |
| `GET` | `/users/me` | Bắt buộc | Đọc hồ sơ |
| `PATCH` | `/users/me` | Bắt buộc | Đổi họ tên |
| `GET` | `/dishes` | Tùy chọn | Danh mục/tìm kiếm/lọc |
| `GET` | `/dishes/{slug}` | Tùy chọn | Chi tiết và công thức |
| `GET` | `/favorites` | Bắt buộc | Danh sách yêu thích |
| `POST` | `/favorites` | Bắt buộc | Thêm yêu thích |
| `DELETE` | `/favorites/{slug}` | Bắt buộc | Bỏ yêu thích |
| `GET` | `/history` | Bắt buộc | Lịch sử nhận diện |
| `DELETE` | `/history` | Bắt buộc | Xóa lịch sử của user |
| `DELETE` | `/history/{id}` | Bắt buộc | Xóa một mục lịch sử |
| `POST` | `/predictions/{id}/feedback` | Bắt buộc | Gửi nhãn đúng |
| `POST` | `/predict` | Tùy chọn | Nhận diện ảnh món |

## Danh mục món

`GET /dishes` hỗ trợ:

- `q`: tìm tên có dấu hoặc không dấu;
- `region`: lọc vùng miền;
- `category`: lọc loại món;
- `difficulty`: lọc độ khó;
- `maxMinutes`: tổng thời gian tối đa;
- `page`: trang, bắt đầu từ 1;
- `limit`: số phần tử, từ 1 đến 100.

`GET /dishes/{slug}` trả metadata món và field `recipe`. `recipe` chỉ khác
`null` khi bản ghi vượt qua đầy đủ điều kiện xuất bản. `imageUrl` là đường dẫn
tương đối để client ghép với base URL.

## Nhận diện

Request là `multipart/form-data`, field bắt buộc tên `image`. Backend chấp nhận
JPEG/JPG/PNG tối đa 10 MB theo mặc định.

```bash
curl -F "image=@food.jpg" http://127.0.0.1:8000/predict
```

Các field quan trọng trong response:

```json
{
  "success": true,
  "prediction": {"dish": "Pho", "confidence": 0.91, "accepted": true},
  "top3": [],
  "predictionId": null,
  "canonicalDish": "Phở",
  "recognizedDish": {"slug": "pho", "name": "Phở"},
  "recipe": {},
  "recipeMessage": null
}
```

`top3` được giữ cho tương thích nội bộ, lịch sử và đánh giá; giao diện chính
chỉ hiển thị Top 1. Nếu nhãn model không ánh xạ được sang catalog,
`recognizedDish` là `null` và client không được tự chọn món khác.

Nếu request có access token hợp lệ, backend lưu lịch sử và trả
`predictionId`. Ảnh không được lưu; `imageStored` luôn là `false` trong luồng
hiện tại.

## Mã lỗi đáng chú ý

| Mã | Trường hợp |
| ---: | --- |
| 400 | Payload nghiệp vụ không hợp lệ |
| 401 | Thiếu/hết hạn token hoặc thông tin đăng nhập sai |
| 404 | Không tìm thấy món, lịch sử hoặc tài nguyên của user |
| 409 | Email đã tồn tại hoặc xung đột dữ liệu |
| 413 | Ảnh lớn hơn giới hạn |
| 415 | Loại media không được hỗ trợ |
| 422 | Ảnh hỏng hoặc request không qua validation |
| 429 | Vượt rate limit |
| 503 | Model chưa sẵn sàng |

Contract chính xác và schema cập nhật nhất luôn có tại `/docs` khi backend
đang chạy.
