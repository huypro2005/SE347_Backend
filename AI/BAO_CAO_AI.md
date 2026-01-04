# BÁO CÁO PHẦN AI - HỆ THỐNG DỰ ĐOÁN GIÁ BẤT ĐỘNG SẢN

## 1. TỔNG QUAN

Phần AI của dự án SE347_Backend được thiết kế để xây dựng một pipeline hoàn chỉnh từ thu thập dữ liệu đến huấn luyện mô hình dự đoán **giá theo triệu/m²** cho bất động sản tại TP. Hồ Chí Minh. Hệ thống sử dụng kỹ thuật web scraping, xử lý dữ liệu và machine learning để tạo ra mô hình dự đoán chính xác.

## 2. KIẾN TRÚC PIPELINE

Pipeline được chia thành 6 giai đoạn chính:

### 2.1. Thu thập Link (Crawling)
- **File**: `GetLinkNhaDat.py`
- **Chức năng**: Thu thập các link tin đăng bất động sản từ website batdongsan.com.vn
- **Phương pháp**: 
  - Sử dụng Selenium với undetected-chromedriver để tránh phát hiện bot
  - Hỗ trợ multithreading với ThreadPoolExecutor (mặc định 6 workers)
  - Có cơ chế retry (tối đa 3 lần) khi gặp lỗi
  - Tự động quản lý và đóng Chrome processes để tránh rò rỉ bộ nhớ
- **Đầu ra**: File `linkNhaDat.txt` chứa danh sách các URL đã crawl

### 2.2. Scrape Chi tiết
- **File**: `LocDataLink.py` (được đề cập trong README nhưng không có trong thư mục)
- **Chức năng**: Đọc từng link trong `linkNhaDat.txt`, lấy thông tin chi tiết của từng tin đăng
- **Đầu ra**: File `data1.json` (JSONL format - mỗi dòng là một đối tượng JSON)

### 2.3. Chuyển đổi Format
- **File**: `json_to_csv.py`
- **Chức năng**: Chuyển đổi dữ liệu từ JSONL sang CSV
- **Các trường dữ liệu**:
  - `loại nhà đất`: Phân loại bất động sản
  - `địa chỉ`: Mã hóa địa chỉ
  - `giá`: Giá bán (triệu đồng)
  - `diện tích`: Diện tích (m²)
  - `giá/m2`: Giá trên mỗi m² (triệu đồng/m²) - **biến mục tiêu**
  - `mặt tiền`: Chiều rộng mặt tiền (m)
  - `phòng ngủ`: Số phòng ngủ
  - `pháp lý`: Trạng thái pháp lý
  - `tọa độ x`: Tọa độ vĩ độ (đã scale)
  - `tọa độ y`: Tọa độ kinh độ (đã scale)
  - `số tầng`: Số tầng của công trình
- **Đầu ra**: File `data_1.csv`

### 2.4. Loại bỏ Trùng lặp (Deduplication)
- **File**: `dedup_data.py`
- **Chức năng**: Loại bỏ các bản ghi trùng lặp trong dữ liệu
- **Hai phương pháp**:
  - **Exact deduplication**: Loại bỏ các hàng trùng lặp hoàn toàn
  - **Fuzzy deduplication**: 
    - Nhóm các bản ghi theo tọa độ đã làm tròn (scale factor)
    - Trong mỗi nhóm, loại bỏ các bản ghi có giá và diện tích tương tự (trong ngưỡng tolerance)
    - Có thể chọn giữ bản ghi đầu tiên, cuối cùng, hoặc có diện tích lớn nhất
- **Tham số tùy chỉnh**:
  - `--coord-scale`: Scale factor để làm tròn tọa độ (mặc định: 1000)
  - `--price-tol`: Ngưỡng tolerance cho giá (mặc định: 0.05 = 5%)
  - `--area-tol`: Ngưỡng tolerance cho diện tích (mặc định: 0.10 = 10%)
- **Đầu ra**: File `data_1.dedup.csv`

### 2.5. Tiền xử lý Dữ liệu
- **Chức năng**: Làm sạch và chuẩn hóa dữ liệu trước khi huấn luyện
- **Các bước xử lý** (thực hiện trong `train_model.py`):
  - Chuyển giá trị 'X' thành NaN
  - Chuyển các cột số sang kiểu float
  - Loại bỏ cột 'giá' (chỉ giữ lại 'giá/m2' làm target)
  - Loại bỏ các dòng thiếu giá trị 'giá/m2'
  - Xử lý logic nghiệp vụ:
    - Loại nhà đất = 7, 6, 9: gán phòng ngủ = 0, số tầng = 0
    - Loại nhà đất = 0: gán mặt tiền = 0, số tầng = 0
  - Điền giá trị thiếu:
    - `mặt tiền`, `phòng ngủ`, `pháp lý`, `số tầng`: điền 0

### 2.6. Huấn luyện Mô hình
- **File**: `train_model.py`
- **Mô hình**: Random Forest Regressor
- **Tham số**:
  - `n_estimators`: 100 cây quyết định
  - `random_state`: 42 (để đảm bảo reproducibility)
- **Chia dữ liệu**: Train/Test split với tỷ lệ 80/20
- **Đánh giá**:
  - MAE (Mean Absolute Error)
  - R² Score (Coefficient of Determination)
- **Đầu ra**: File `model.pkl` (kích thước ~65MB)

## 3. CÔNG NGHỆ SỬ DỤNG

### 3.1. Thư viện Python
- **pandas**: Xử lý và phân tích dữ liệu
- **scikit-learn**: Machine learning (RandomForestRegressor, metrics)
- **joblib**: Lưu và tải mô hình
- **beautifulsoup4**: Parse HTML
- **selenium**: Tự động hóa trình duyệt
- **undetected-chromedriver**: Tránh phát hiện bot
- **psutil**: Quản lý processes
- **lxml**: Parser XML/HTML

### 3.2. Kỹ thuật
- **Web Scraping**: Selenium + BeautifulSoup
- **Multithreading**: ThreadPoolExecutor cho crawling song song
- **Error Handling**: Retry mechanism với exponential backoff
- **Memory Management**: Tự động đóng Chrome processes
- **Data Cleaning**: Xử lý missing values, normalization
- **Machine Learning**: Ensemble method (Random Forest)

## 4. QUY TRÌNH SỬ DỤNG

### 4.1. Cài đặt Môi trường
```bash
python -m pip install -r requirements.txt
# hoặc
python -m pip install pandas scikit-learn joblib beautifulsoup4 undetected-chromedriver selenium psutil lxml
```

### 4.2. Chạy Pipeline (Thứ tự đề nghị)

1. **Crawl link** (ghi thêm vào `linkNhaDat.txt`):
   ```bash
   python GetLinkNhaDat.py
   ```

2. **Scrape chi tiết vào JSON**:
   ```bash
   python LocDataLink.py
   ```

3. **Chuyển JSON -> CSV**:
   ```bash
   python json_to_csv.py
   ```

4. **Loại trùng**:
   ```bash
   # Exact deduplication
   python dedup_data.py --input data_1.csv --method exact
   
   # Fuzzy deduplication
   python dedup_data.py --input data_1.csv --method fuzzy --coord-scale 1000 --price-tol 0.05 --area-tol 0.10
   ```

5. **Huấn luyện mô hình**:
   ```bash
   python train_model.py
   ```

## 5. ĐẶC ĐIỂM KỸ THUẬT

### 5.1. Xử lý Lỗi và Retry
- Mỗi request có cơ chế retry tối đa 3 lần
- Delay giữa các request để tránh bị block (1 giây giữa các trang)
- Tự động đóng và kill Chrome processes khi gặp lỗi

### 5.2. Tối ưu Hiệu suất
- Multithreading cho crawling (6 workers mặc định)
- Batch processing cho việc ghi file
- Efficient memory management

### 5.3. Xử lý Dữ liệu
- Logic nghiệp vụ được encode trong quá trình tiền xử lý
- Xử lý missing values thông minh dựa trên loại nhà đất
- Scale tọa độ để phù hợp với mô hình (nhân với 10^9)

### 5.4. Mô hình Machine Learning
- Random Forest phù hợp cho bài toán regression với dữ liệu có nhiều features
- Không cần feature scaling (tree-based model)
- Có khả năng xử lý missing values tốt

## 6. LƯU Ý VÀ CẢNH BÁO

### 6.1. Đạo đức và Pháp lý
- Tuân thủ robots.txt và chính sách của website
- Thêm delay giữa các request để tránh gây quá tải server
- Sử dụng undetected-chromedriver có thể vi phạm Terms of Service của một số website

### 6.2. Kỹ thuật
- `model.pkl` có kích thước lớn (~65MB), nên sử dụng Git LFS nếu cần version control
- Các script có hành vi append, cần sao lưu dữ liệu trước khi chạy lại
- `train_model.py` kỳ vọng dữ liệu đã được tiền xử lý, cần kiểm tra đường dẫn file đầu vào

### 6.3. Dữ liệu
- Đảm bảo Chrome tương thích với undetected-chromedriver
- Kiểm tra encoding UTF-8 cho các file text
- Validate dữ liệu trước khi đưa vào mô hình

## 7. KẾT QUẢ VÀ ĐÁNH GIÁ

### 7.1. Dữ liệu Thu thập
- Hệ thống có khả năng crawl hàng nghìn trang từ batdongsan.com.vn
- Dữ liệu được lưu trữ dưới dạng JSONL và CSV để dễ xử lý

### 7.2. Mô hình
- Mô hình Random Forest đã được huấn luyện và lưu thành công
- Có thể sử dụng mô hình để dự đoán giá/m² cho bất động sản mới
- Ví dụ test case trong code cho thấy cách sử dụng mô hình

### 7.3. Metrics
- MAE và R² được sử dụng để đánh giá hiệu suất mô hình
- Cần chạy `train_model.py` để xem kết quả cụ thể

## 8. HƯỚNG PHÁT TRIỂN

### 8.1. Cải thiện Mô hình
- Thử nghiệm các mô hình khác (XGBoost, LightGBM, Neural Networks)
- Tối ưu hyperparameters
- Feature engineering nâng cao (tạo thêm features từ tọa độ, địa chỉ)

### 8.2. Cải thiện Pipeline
- Thêm validation pipeline
- Tự động hóa toàn bộ quy trình
- Thêm monitoring và logging
- Tích hợp với database thay vì file CSV

### 8.3. Mở rộng Chức năng
- Hỗ trợ nhiều khu vực hơn (không chỉ TP.HCM)
- Dự đoán nhiều loại giá trị khác (giá tổng, xu hướng giá)
- API endpoint để sử dụng mô hình
- Dashboard để visualize kết quả

## 9. KẾT LUẬN

Phần AI của dự án SE347_Backend đã xây dựng thành công một pipeline hoàn chỉnh từ thu thập dữ liệu đến huấn luyện mô hình dự đoán giá bất động sản. Hệ thống sử dụng các công nghệ hiện đại, có cơ chế xử lý lỗi tốt và có khả năng mở rộng. Mô hình Random Forest đã được huấn luyện và sẵn sàng sử dụng để dự đoán giá/m² cho các bất động sản mới.

---

**Ngày tạo báo cáo**: $(date)
**Phiên bản**: 1.0
**Tác giả**: Hệ thống AI Documentation

