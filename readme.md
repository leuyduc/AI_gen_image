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

# Ứng dụng Desktop Tạo Ảnh AI

> **Ứng dụng desktop xây dựng bằng `customtkinter` cho phép tạo ảnh từ mô tả văn bản thông qua API AI, hỗ trợ chỉnh sửa ảnh cơ bản và lưu lịch sử tìm kiếm – đóng gói thành một file thực thi duy nhất bằng PyInstaller.**

---

## Mục lục
1. [Tính năng](#tính-năng)
2. [Công nghệ sử dụng](#công-nghệ-sử-dụng)
3. [Cấu trúc dự án](#cấu-trúc-dự-án)
4. [Thiết lập cục bộ](#thiết-lập-cục-bộ)
5. [Chạy ứng dụng](#chạy-ứng-dụng)
6. [Đóng gói file thực thi](#đóng-gói-file-thực-thi)
7. [Lược đồ cơ sở dữ liệu](#lược-đồ-cơ-sở-dữ-liệu)
8. [Lộ trình phát triển](#lộ-trình-phát-triển)
9. [Khắc phục sự cố & FAQ](#khắc-phục-sự-cố--faq)


---

## Tính năng
| # | Khả năng | Chi tiết |
|---|----------|----------|
| 1 | **Từ prompt → Ảnh** | Gửi prompt văn bản tới API AI (OpenAI DALL·E, Stability, Replicate…). Ảnh trả về được hiển thị tức thì. |
| 2 | **Tải & chỉnh sửa** | Nhập ảnh local và thực hiện <br> • Cắt (Crop). |
| 3 | **Lịch sử** | Mọi lần sinh/chỉnh sửa ảnh được lưu vào SQLite với prompt, đường dẫn file & thời gian; hiển thị trong bảng có ô tìm kiếm. |
| 4 | **Xuất ảnh** | Lưu thành PNG/JPG hoặc copy vào clipboard. |
| 5 | **Đóng gói 1‑click** | Phát hành `.exe`/`.app` độc lập qua PyInstaller. |

---

## Công nghệ sử dụng
| Tầng | Lựa chọn |
|------|----------|
| Giao diện | **customtkinter** (wrapper Tk hiện đại) |
| AI API | Đóng gói trong `core/api_client.py` – có thể hoán đổi nhà cung cấp qua cài đặt ứng dụng. |
| Xử lý ảnh | **Pillow (PIL)** |
| CSDL cục bộ | **SQLite** (`sqlite3` stdlib) |
| HTTP | `requests` (sync) hoặc `httpx` (async) |
| Đóng gói | **PyInstaller** (`--onefile --noconsole`) |
| Công cụ | `logging`, **pytest** |

---

## Cấu trúc dự án
```text
aI_image_app/
├── core/
│   ├── api_client.py      # gọi AI, logic retry
│   ├── image_editor.py    # crop
│   ├── db.py              # CRUD & tìm kiếm SQLite
│   └── settings.py        # quản lý config.json & đường dẫn
├── ui/
│   ├── main_window.py     # cửa sổ gốc + thanh điều hướng
│   ├── generate_tab.py    # prompt & preview
│   ├── edit_tab.py        # canvas chỉnh sửa
│   └── history_tab.py     # bảng lịch sử + search
├── resources/
│   └── app_icon.ico
├── tests/
│   └── test_db.py
├── main.py
└── requirements.txt
```

---

## Thiết lập cục bộ
```bash
# 1. Clone & tạo virtual env

python -m venv .venv   # Windows: .venv\Scripts\activate

# 2. Cài đặt phụ thuộc
pip install -r requirements.txt

# 3. Khởi động ứng dụng và cấu hình API
# Ứng dụng sẽ tự tạo file config.json tại thư mục ~/Pictures/AI_App/
```

---

## Chạy ứng dụng
```bash
python main.py
```
Cửa sổ chính sẽ mở với ba tab **Generate / Edit / History**. Nhập prompt, bấm **Generate** và thưởng thức ✨.

---

## Đóng gói file thực thi
```bash
# Ví dụ Windows – chạy tại thư mục gốc dự án
pyinstaller --onefile --noconsole ^
            --add-data "resources/app_icon.ico;resources" ^
            --icon resources/app_icon.ico ^
            --name AIImageGenerator main.py
```
File `dist/AIImageGenerator.exe` tạo ra có thể được phân phối như một file portable.

> **Mẹo:** thêm script `build.bat` (Windows) chứa lệnh trên để build lặp lại.

---

## Lược đồ cơ sở dữ liệu
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
Ảnh mặc định lưu tại `~/Pictures/AI_App/YYYY-MM-DD/` (có thể đổi trong `settings.py`).

---

## Lộ trình phát triển
| Tuần | Hạng mục | Kết quả |
|------|----------|---------|
| 1 | Khởi tạo repo · Lớp DB · skeleton GUI | Cửa sổ app trống, điều hướng được |
| 2 | Tích hợp AI API | Hoàn thiện tab Generate |
| 3 | Chỉnh sửa ảnh (Pillow) · Tab History | Đủ tính năng chính |
| 4 | Kiểm thử · Tài liệu · PyInstaller build | Phát hành v1.0 |

---

## Khắc phục sự cố & FAQ
<details>
<summary>PyInstaller thiếu DLL</summary>
Thêm bằng `--add-binary` hoặc tạo file hook. Lỗi thường gặp: `msvcp140.dll` trên Windows.
</details>

<details>
<summary>Lỗi quota/timeout API</summary>
`api_client.py` đã retry theo cấp số nhân. Kiểm tra API key và hạn mức, sau đó thử lại.
</details>

---


