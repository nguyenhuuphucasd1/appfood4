# Báo cáo kiểm tra project ban đầu (lịch sử)

> Tài liệu này ghi lại trạng thái workspace tại ngày 27/09/2026, trước khi
> backend FastAPI và ứng dụng Flutter hiện tại được hoàn thiện. Một số nhận
> định bên dưới không còn phản ánh trạng thái mới nhất. Xem `README.md` ở thư
> mục gốc và các tài liệu trong `docs/` để biết cấu trúc đang sử dụng.

Ngày kiểm tra: 2026-09-27

## 1. Framework và source hiện có

- Không tìm thấy `pubspec.yaml`, `android/`, `build.gradle`, `settings.gradle`, `AndroidManifest.xml` hoặc source mobile.
- Vì vậy workspace hiện tại **không phải Flutter và cũng không phải Android Native**.
- Không có màn hình mobile, camera, gallery, permission, API service mobile hay cấu hình endpoint mobile để giữ lại hoặc sửa.
- Workspace ban đầu không phải Git working tree.

Theo yêu cầu không tự ý đổi/chọn framework, không tạo mới app mobile khi chưa có source mobile.

## 2. Nội dung ban đầu

Workspace chỉ có `30VNFoods-main/`, gồm 27 file:

- `app.py`: demo Streamlit cũ, dùng TensorFlow và model path placeholder.
- `requirements.txt`: `plotly==4.8.0`, `tensorflow==2.4.0`.
- 5 notebook thử nghiệm model cũ.
- mã Google Sheets hỗ trợ labeling.
- README, license, PDF hướng dẫn.

Không có backend hoạt động sẵn, database, recipe service hoặc recipe dataset.

## 3. Kiểm tra 30VNFoods local

- Vị trí hiện tại: `datasets/30VNFoods-main/`.
- Tổng số file: 27.
- Tổng file ảnh: 11 (`10 .jpg`, `1 .png`).
- 11 ảnh này là biểu đồ kiến trúc/model và ảnh giao diện labeling; không phải ảnh món ăn có ground truth.
- Số thư mục class ảnh phát hiện được: **0**.
- Số ảnh món ăn có nhãn có thể test: **0**.

README upstream mô tả dataset 25.136 ảnh/30 món, còn `app.py` cũ có danh sách tham khảo 30 nhãn. Các con số đó không được coi là nội dung ảnh đang có trong workspace.

## 4. Model pretrained đã kiểm tra

- Model: `VietTung04/vit-l-16-food-classifier`.
- Architecture: `ViTForImageClassification` (ViT-L/16).
- Model type: `vit`.
- Input: RGB 384×384 do `ViTImageProcessor` resize/rescale/normalize.
- Labels: 38 nhãn, đọc từ `model.config.id2label`.
- Trọng số local: `model.safetensors`, 1.214.965.360 byte.
- Thiết bị môi trường hiện tại: CPU; không có CUDA.

## 5. Thành phần đã bổ sung

- FastAPI: `GET /health`, `POST /predict`, Swagger `/docs`.
- Model singleton load lúc backend khởi động, ưu tiên local và tự tải khi thiếu.
- Decode JPEG/JPG/PNG, RGB, processor chính thức, `torch.inference_mode()`.
- Top-3 và `CONFIDENCE_THRESHOLD` tập trung tại `backend/config.py`.
- Name normalizer + alias file rỗng để mở rộng có kiểm soát.
- `RecipeRepository` rỗng; API trả `recipe: null`, không tạo công thức giả.
- Script download, audit dataset, đánh giá mẫu, test model độc lập.
- Script cài/chạy backend trên Windows.

## 6. Kết quả test

- Compile Python: PASS.
- Unit/API regression: PASS (7/7).
- Model download/local validation: PASS.
- Model inference trên CPU: PASS.
- HTTP health/predict/docs: PASS.
- MIME không hỗ trợ: HTTP 415 PASS.
- Ảnh hỏng: HTTP 422 PASS.
- Đánh giá bằng ảnh 30VNFoods có ground truth: NOT TESTED — ảnh dataset không có trong workspace.
- Mobile build/camera/gallery/emulator: PASS sau khi bổ sung project Flutter và kiểm thử trên AVD Android.

## 7. Cập nhật giao diện Flutter

Sau audit ban đầu, người dùng yêu cầu tạo UI mobile theo mẫu. Project Flutter đã được tạo tại `mobile/` với:

- đăng nhập và đăng ký;
- trang chủ, danh mục và thẻ món ăn;
- màn chi tiết không tạo công thức giả;
- chụp ảnh/chọn ảnh, preview và loading;
- gọi multipart `POST /predict`;
- màn kết quả confidence, Top-3 và trạng thái confidence thấp;
- endpoint Android Emulator mặc định `http://10.0.2.2:8000`.

Kết quả mới: `flutter analyze` PASS, widget/golden test PASS, APK debug PASS. App đã build, cài và chạy trên AVD `Medium_Phone` (Android 17/API 37). Luồng chọn ảnh phở từ Photo Picker, upload multipart tới FastAPI qua `10.0.2.2:8000`, suy luận model và hiển thị Top-3 đã PASS (`Pho` khoảng 85,7%). Quyền camera, mở camera ảo, chụp, trả ảnh về app và gửi ảnh camera tới API đều PASS; ảnh cảnh ảo không phải món ăn cho confidence thấp 13,6% và app hiển thị đúng trạng thái chưa đủ chắc chắn. Thiết bị Android thật vẫn NOT TESTED.

Android Studio có sẵn cấu hình Flutter `main.dart`. Sau khi người dùng tự mở AVD `Medium_Phone`, nhấn Shift+F10 sẽ build, cài và chạy app trên emulator. Backend được chạy thủ công bằng `run_backend.bat`, không gắn tự động vào Gradle.
