# Pipeline AI — SE347_Backend/AI

Thư mục này chứa các bước thu thập dữ liệu, tiền xử lý và mô hình dự đoán **giá theo triệu/m2** cho bất động sản (TP. HCM).

## Tổng quan 
- Crawl: thu thập link tin bằng `GetLinkNhaDat.py` (crawl theo trang) và lưu vào `linkNhaDat.txt`.
- Scrape chi tiết: `LocDataLink.py` đọc `linkNhaDat.txt`, lấy chi tiết từng tin và ghi thành JSON (mỗi dòng một đối tượng) vào `data1.json`.
- Chuyển đổi: `json_to_csv.py` chuyển `data1.json` thành `data_1.csv`.
- Loại trùng: `dedup_data.py` loại bỏ bản ghi trùng (exact hoặc fuzzy) và ghi `data_1.dedup.csv`.
- Tiền xử lý: sử dụng script tiền xử lý (ví dụ `preprocess_data.py`) để làm sạch và tạo features.
- Huấn luyện: `train_model.py` huấn luyện mô hình RandomForest và lưu kết quả dưới dạng `model.pkl`.

## Các tập tin quan trọng 
- `linkNhaDat.txt` — các URL đã crawl (đã thêm)
- `data1.json` — kết quả scrape (JSONL)
- `data_1.csv` — CSV chuyển từ JSON
- `data_1.dedup.csv` — CSV đã loại trùng
- `json_to_csv.py`, `GetLinkNhaDat.py`, `LocDataLink.py`, `dedup_data.py` — script pipeline
- `train_model.py` — script huấn luyện (lưu model dưới tên `model.pkl`)
- `model.pkl` — mô hình đã huấn luyện (đã thêm/ghi đè theo yêu cầu)

## Yêu cầu nhanh 
- Python 3.8+
- Thư viện: `pandas`, `scikit-learn`, `joblib`, `beautifulsoup4`, `undetected-chromedriver`, `selenium`, `psutil`, `lxml`

Cài đặt:

```bash
python -m pip install -r requirements.txt
# hoặc
python -m pip install pandas scikit-learn joblib beautifulsoup4 undetected-chromedriver selenium psutil lxml
```

Lưu ý:
- `undetected-chromedriver` và `selenium` điều khiển Chrome; đảm bảo Chrome tương thích với driver.
- Khi chạy crawler trên diện rộng, tuân thủ robots.txt và chính sách site; thêm delay để tránh bị block.

## Hướng dẫn sử dụng (thứ tự đề nghị) 
1. Crawl link (ghi thêm vào `linkNhaDat.txt`):
   ```bash
   python GetLinkNhaDat.py
   ```
2. Scrape chi tiết vào JSON:
   ```bash
   python LocDataLink.py
   ```
3. Chuyển JSON -> CSV:
   ```bash
   python json_to_csv.py
   ```
4. Loại trùng:
   ```bash
   python dedup_data.py --input data_1.csv --method exact
   # hoặc fuzzy:
   python dedup_data.py --input data_1.csv --method fuzzy --coord-scale 1000 --price-tol 0.05 --area-tol 0.10
   ```
5. Tiền xử lý: chạy script tiền xử lý để tạo CSV huấn luyện phù hợp.
6. Huấn luyện mô hình:
   ```bash
   python train_model.py
   ```

## Ghi chú & cảnh báo 
- `train_model.py` kỳ vọng dữ liệu đã được tiền xử lý; kiểm tra đường dẫn file đầu vào nếu gặp lỗi.
- `json_to_csv.py` và `LocDataLink.py` có hành vi ghi/appending; sao lưu dữ liệu tránh trùng khi chạy lại.
- `model.pkl` lớn (~65MB) đã được commit; nếu các mô hình tiếp theo lớn hơn, cân nhắc dùng Git LFS.


