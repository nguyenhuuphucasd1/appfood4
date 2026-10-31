# Model nhận diện và dataset 30VNFoods

## Hai phạm vi khác nhau

Model production và dataset 30VNFoods không có cùng số lớp:

- model production: 38 nhãn;
- 30VNFoods: 30 lớp;
- 30 lớp dataset đều ánh xạ được sang model;
- 8 nhãn model không có trong dataset: Bánh cu đơ, Nem nướng, Bánh mì cay,
  Cơm cháy, Bò bía, Bánh đậu xanh, Bánh đa cua và Bún cá.

Vì vậy 30VNFoods dùng để audit, đánh giá và huấn luyện candidate trên phần giao
nhau; không được ghi đè model production 38 nhãn.

## Model production

- Hugging Face: `VietTung04/vit-l-16-food-classifier`;
- kiến trúc: `ViTForImageClassification` (ViT-L/16);
- input: RGB 384×384;
- local path: `backend/models/vietnamese_food_classifier/`;
- trọng số khoảng 1,21 GB;
- loader dùng singleton và `torch.inference_mode()`;
- processor lấy từ metadata chính thức của model.

Model/candidate bị loại khỏi Git vì dung lượng lớn. `setup_backend.bat` hoặc
`backend/scripts/download_model.py` tải model khi môi trường mới chưa có.

## Nguồn dataset

- Kaggle: `quandang/vietnamese-foods`;
- local raw: `datasets/raw/30VNFoods/`;
- upstream code tham khảo: `datasets/30VNFoods-main/`;
- license gói tải: file `LICENSE` đi kèm dataset;
- mục đích trong project: train/validation/test và đánh giá, không làm ảnh UI.

Mọi token và cache Kaggle phải ở `D:\appfood4\.kaggle` và
`D:\appfood4\.cache`; script không chủ động tìm credential ở ổ C.

## Kết quả audit ngày 06/10/2026

| Thuộc tính | Kết quả |
| --- | ---: |
| Tổng dung lượng giải nén | khoảng 4,20 GB |
| Số lớp | 30 |
| Tổng ảnh có nhãn | 25.136 |
| Train | 17.581 |
| Validate | 2.515 |
| Test | 5.040 |
| Ảnh Pillow đọc được | 25.136 |
| Ảnh hỏng | 0 |
| Nhóm trùng SHA-256 | 63 |
| Bản sao thừa | 66 |
| Nhóm trùng qua nhiều split | 40 |
| Nhóm giống ảnh nhưng khác nhãn | 38 |

Báo cáo máy đọc nằm ở `artifacts/data_audit/30vnfoods_audit.json`.

## Split sạch

Raw không bị sửa. Manifest sạch tại
`datasets/processed/30VNFoods_clean/manifests/` còn 25.032 ảnh:

- Train: 17.515;
- Validate: 2.503;
- Test: 5.014.

Với ảnh trùng đúng nhãn, chỉ giữ một bản. Nếu trùng qua nhiều split thì ưu tiên
Test, sau đó Validate, rồi Train để tránh rò rỉ ảnh đánh giá. Nhóm trùng nhưng
mâu thuẫn nhãn bị loại hoàn toàn khỏi manifest sạch.

## Đánh giá mẫu hiện có

Đã chạy 30 ảnh thuộc tập Test, mỗi lớp một ảnh:

- đúng 28/30 (93,33% trên mẫu nhỏ);
- confidence trung bình 92,61%;
- hai mẫu sai: Bánh mì → Bánh khọt và Phở → Cháo lòng.

Đây không phải accuracy của toàn bộ tập Test và không được dùng để tuyên bố
hiệu năng tổng thể. File kết quả nằm tại
`artifacts/evaluation/sample_30_test.csv`.

## Chạy lại audit

```bat
scripts\configure_ml_storage.bat
.venv\Scripts\python backend\scripts\audit_dataset.py datasets\raw\30VNFoods --output artifacts\data_audit\30vnfoods_audit.json --verify-images --find-duplicates
.venv\Scripts\python backend\scripts\compare_dataset_labels.py datasets\raw\30VNFoods backend\models\vietnamese_food_classifier\config.json --output artifacts\data_audit\label_mapping_30_to_38.json
.venv\Scripts\python backend\scripts\create_clean_split_manifest.py datasets\raw\30VNFoods datasets\processed\30VNFoods_clean\manifests
.venv\Scripts\python backend\scripts\evaluate_dataset.py datasets\raw\30VNFoods --split Test --per-class 1 --output artifacts\evaluation\sample_30_test.csv
```

Đánh giá đầy đủ trên CPU có thể mất nhiều thời gian. Khi fine-tune, luôn ghi
checkpoint vào `backend/models/candidates/` hoặc `artifacts/training/` và chỉ
thay model production sau một quy trình nghiệm thu riêng.
