# Báo cáo đồ án Vị Việt

Thư mục này là báo cáo LaTeX độc lập của đề tài **Xây dựng hệ thống gợi ý và
tìm kiếm công thức nấu ăn**. Mã nguồn ứng dụng được đọc từ `D:\appfood4` nhưng
không bị thay đổi khi biên dịch báo cáo.

## Thông tin bìa đã điền

Các thông tin đang được khai báo trong `do-an.tex`:

- `NGUYỄN HỮU PHÚC`
- `2351220005`
- `23CT1`
- `TS. Đỗ Phúc Hảo`
- `2026--2027`

## Biên dịch bằng TeXstudio/MiKTeX

Chọn `XeLaTeX` làm compiler. Nếu có `latexmk`, chạy:

```powershell
latexmk -xelatex do-an.tex
```

Nếu không có `latexmk`, chạy lần lượt:

```powershell
xelatex -disable-installer do-an.tex
bibtex -disable-installer do-an
xelatex -disable-installer do-an.tex
xelatex -disable-installer do-an.tex
```

Hoặc chạy trực tiếp `build_report.bat`; script sẽ dừng khi một bước biên dịch
thất bại và tạo `BaoCao-DoAn-ViViet.pdf` khi thành công.
Tùy chọn `-disable-installer` bảo đảm quá trình build không tự tải package
hoặc mở hộp thoại cài đặt của MiKTeX.

## Xuất bộ hình độc lập

Chạy `tools\export_images.bat` để xuất 16 hình, mỗi hình có PNG và PDF, sang
`D:\BaoCaoViViet-HinhAnh`. Sáu PDF sơ đồ là vector TikZ; bốn biểu đồ và sáu
ảnh giao diện được đóng gói thành PDF một trang. `manifest.csv` ghi kích
thước, dung lượng, SHA-256 và file nguồn của từng định dạng. Toàn bộ file tạm
được đặt trong `build/figure-export`.

## Đánh giá model

Đánh giá đầy đủ đọc manifest sạch 5.014 ảnh và hỗ trợ tiếp tục từ checkpoint:

```powershell
D:\appfood4\.venv\Scripts\python.exe tools\evaluate_full_test.py `
  --project D:\appfood4 `
  --report D:\BaoCaoViViet `
  --batch-size 4
```

Kết quả được ghi vào `evaluation/`; biểu đồ được ghi vào `figs/charts/`.
Không xóa `evaluation/predictions.csv` giữa chừng nếu muốn tiếp tục lần chạy.

## Quy tắc số liệu

- Chỉ dùng số liệu có trong database, audit, log test hoặc kết quả đánh giá.
- Không thay kết quả 5.014 ảnh bằng mẫu 30 ảnh.
- Độ đo chỉ đại diện 30 lớp giao nhau với 30VNFoods, không phải đủ 38 lớp.
- Ảnh người dùng gửi `/predict` không được lưu.
