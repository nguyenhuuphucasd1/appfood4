# Dữ liệu, nguồn và giấy phép

## Nguyên tắc

Vị Việt không xuất bản công thức hoặc ảnh chỉ vì tên món tồn tại trong model.
Mỗi món phải có dữ liệu có thể truy nguyên và vượt qua audit. Dữ liệu train
không được dùng tự động làm ảnh minh họa vì giấy phép cấp bộ dữ liệu không thay
thế metadata quyền sử dụng của từng ảnh trong giao diện.

## Catalog công thức

Catalog nguồn nằm trong `backend/data/recipes/`:

- `open_recipes.vi.json`: 8 món được dịch và chuẩn hóa từ phiên bản cố định của
  Wikibooks;
- `verified_recipes.vi.json`: 30 món do Vị Việt biên soạn mới bằng tiếng Việt,
  đối chiếu ít nhất hai nguồn cho mỗi món;
- `media_manifest.json`: URL file, tác giả, giấy phép, URL giấy phép và SHA-256
  của ảnh;
- `LICENSE.md`: thông báo attribution/ShareAlike cho nội dung công thức.

Nội dung dịch ghi rõ đã thay đổi so với nguồn. Nội dung biên soạn không sao
chép nguyên văn và không tuyên bố đã được chuyên gia ẩm thực kiểm duyệt.

## Điều kiện xuất bản

Importer và serializer chỉ cho `hasRecipe=true` khi có:

- tên nguồn, URL nguồn và URL phiên bản;
- tên giấy phép, URL giấy phép và attribution;
- nguồn gốc nội dung, trạng thái và ghi chú xác minh;
- ít nhất một nguyên liệu và một bước nấu;
- ảnh local với tác giả, URL nguồn, tên giấy phép và URL giấy phép;
- tối thiểu một reference cho nội dung dịch từ nguồn mở;
- tối thiểu hai reference cho nội dung Vị Việt biên soạn.
- `prepMinutes`, `cookMinutes`, `totalMinutes` và `servingsText` có nguồn rõ
  ràng; URL cung cấp metadata phải xuất hiện trong danh sách reference.

Catalog hiện đạt 38/38 món có thời gian sơ chế, nấu, tổng thời gian và khẩu
phần. `cookMinutes=0` biểu thị món không cần nấu; `null` vẫn dành cho dữ liệu cũ
chưa có. Thời gian chờ/ngâm/lên men được giữ trong tổng thời gian khi nguồn tính
phần đó. Trường độ khó không thuộc đợt chuẩn hóa này và vẫn có thể là `null`.

## Ảnh món ăn

Ảnh hiển thị được chọn từ Wikimedia Commons/Openverse và chỉ chấp nhận Public
Domain, CC0, CC BY hoặc CC BY-SA. Không chấp nhận NC, ND, fair-use, ảnh thiếu
tác giả/giấy phép hoặc ảnh train. Ảnh được tải về, đổi sang WebP tối ưu và lưu
tại `backend/static/dishes/`; ứng dụng không hotlink ảnh gốc.

Mỗi ảnh cần kiểm tra:

1. nội dung đúng món;
2. file giải mã được và kích thước phù hợp;
3. tác giả và trang nguồn còn truy cập được;
4. giấy phép thuộc danh sách chấp nhận;
5. SHA-256 khớp manifest.

## Phạm vi giấy phép

Điều khoản CC BY-SA áp dụng cho nội dung công thức và phần chuyển thể tương
ứng, không tự động áp lên toàn bộ mã nguồn Vị Việt. Khi phân phối ứng dụng hoặc
trích xuất dữ liệu, cần giữ trang “Nguồn & bản quyền”, attribution, URL nguồn và
URL giấy phép.

## Import và audit

Chạy từ root:

```bat
.venv\Scripts\python -m backend.scripts.download_recipe_images --catalog backend\data\recipes\open_recipes.vi.json backend\data\recipes\verified_recipes.vi.json --output backend\data\recipes\media_manifest.json
.venv\Scripts\python -m backend.scripts.import_recipes backend\data\recipes\open_recipes.vi.json backend\data\recipes\verified_recipes.vi.json --media-manifest backend\data\recipes\media_manifest.json --dry-run
.venv\Scripts\python -m backend.scripts.import_recipes backend\data\recipes\open_recipes.vi.json backend\data\recipes\verified_recipes.vi.json --media-manifest backend\data\recipes\media_manifest.json
.venv\Scripts\python -m backend.scripts.audit_recipe_data
```

Import thật tự sao lưu SQLite vào `artifacts/backups/`, cập nhật theo `slug` và
chạy trong transaction. Không chỉnh catalog, manifest và ảnh rời nhau mà không
chạy lại audit.

## Dữ liệu cục bộ và Git

Được theo dõi trong Git:

- source code và migration;
- catalog công thức;
- manifest giấy phép;
- `backend/static/dishes/*.webp`;
- tài liệu.

Không được theo dõi trong Git:

- token Kaggle hoặc `.env`;
- database có tài khoản/lịch sử;
- dataset raw/processed;
- model và checkpoint;
- cache, log, backup và artifact kiểm thử.
