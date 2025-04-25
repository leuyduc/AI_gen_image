# AI Image Generator

Ứng dụng tạo hình ảnh sử dụng các API của AI như OpenAI, Stability và Gemini.

## Tính năng

- Tạo hình ảnh từ văn bản mô tả (prompt)
- Lưu trữ và quản lý lịch sử tạo hình ảnh
- Hỗ trợ nhiều API khác nhau: OpenAI (DALL-E), Stability AI, Gemini
- Giao diện người dùng thân thiện với chế độ tối
- Lưu trữ dữ liệu người dùng trong thư mục App_Data

## Cài đặt

### Sử dụng tệp thực thi đã đóng gói

1. Tải xuống tệp thực thi từ phần Releases
2. Giải nén tệp nén vào thư mục mong muốn
3. Chạy file `AI_Image_Generator.exe` trong thư mục giải nén

### Hoặc đóng gói ứng dụng bằng PyInstaller

```bash
# Cài đặt PyInstaller (nếu chưa có)
pip install pyinstaller

# Đóng gói ứng dụng
pyinstaller app.spec
```

Sau khi đóng gói, bạn sẽ tìm thấy tệp thực thi trong thư mục `dist/AI_Image_Generator`.

## Cấu trúc thư mục sau khi đóng gói

```
AI_Image_Generator/
├── AI_Image_Generator.exe  # Tệp thực thi chính
├── App_Data/               # Thư mục lưu trữ dữ liệu người dùng (hình ảnh, cài đặt, cơ sở dữ liệu)
│   ├── YYYY-MM-DD/         # Thư mục lưu hình ảnh theo ngày
│   ├── config.json         # Tệp cấu hình
│   └── history.db          # Cơ sở dữ liệu lịch sử
├── resources/              # Tài nguyên ứng dụng (biểu tượng, hình ảnh)
└── [các thư viện khác]     # Các tệp thư viện phụ thuộc
```

## Sử dụng

1. Mở ứng dụng bằng cách chạy `AI_Image_Generator.exe`
2. Vào tab "API Settings" để cấu hình API key cho nhà cung cấp bạn muốn sử dụng
3. Tại tab "Generate", nhập prompt mô tả hình ảnh bạn muốn tạo
4. Chọn kích thước hình ảnh và nhấn "Generate" để tạo hình ảnh
5. Hình ảnh được tạo sẽ tự động lưu và hiển thị
6. Xem lịch sử các hình ảnh đã tạo tại tab "History"

## Lưu ý

- Tất cả dữ liệu người dùng (hình ảnh, cấu hình, lịch sử) sẽ được lưu trong thư mục `App_Data` bên trong thư mục ứng dụng
- Khi di chuyển ứng dụng, hãy di chuyển toàn bộ thư mục để giữ nguyên dữ liệu

---

## Thông tin kỹ thuật cho nhà phát triển

### Công nghệ sử dụng
| Tầng | Lựa chọn |
|------|----------|
| Giao diện | **customtkinter** (wrapper Tk hiện đại) |
| AI API | Đóng gói trong `core/api_client.py` – có thể hoán đổi nhà cung cấp qua cài đặt ứng dụng. |
| Xử lý ảnh | **Pillow (PIL)** |
| CSDL cục bộ | **SQLite** (`sqlite3` stdlib) |
| HTTP | `requests` |
| Đóng gói | **PyInstaller** |

### Cấu trúc dự án
```text
AI_Image_Generator/
├── core/
│   ├── api_client.py      # gọi AI, logic retry
│   ├── db.py              # CRUD & tìm kiếm SQLite
│   └── settings.py        # quản lý config.json & đường dẫn
├── ui/
│   ├── main_window.py     # cửa sổ chính + thanh điều hướng
│   ├── generate_tab.py    # tab tạo ảnh từ prompt
│   ├── history_tab.py     # tab hiển thị lịch sử + tìm kiếm
│   └── settings_dialog.py # hộp thoại cài đặt API
├── resources/
│   └── image-_1_.ico      # biểu tượng ứng dụng
├── main.py                # điểm khởi đầu ứng dụng
├── app.spec               # cấu hình PyInstaller
├── requirements.txt       # các thư viện phụ thuộc
└── INSTRUCTIONS.txt       # hướng dẫn sử dụng
```

### Lược đồ cơ sở dữ liệu
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    provider TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    width INTEGER,
    height INTEGER,
    extra_data TEXT
);
```

### Khắc phục sự cố & FAQ
<details>
<summary>PyInstaller thiếu DLL</summary>
Thêm bằng `--add-binary` hoặc tạo file hook. Lỗi thường gặp: `msvcp140.dll` trên Windows.
</details>

<details>
<summary>Lỗi quota/timeout API</summary>
`api_client.py` đã retry theo cấp số nhân. Kiểm tra API key và hạn mức, sau đó thử lại.
</details>


