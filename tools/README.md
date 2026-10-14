# Công cụ dùng chung

## preview.html: xem nhanh nhiều tư thế của file GLB

Dùng để kiểm tra hình dáng và animation của model trước khi đưa vào Roblox Studio (ảnh `preview.png` trong mỗi folder model được chụp bằng cách này). Chỉ cần trình duyệt và Python, cần mạng để tải thư viện `model-viewer` từ unpkg.

1. Tại thư mục gốc repo chạy `python -m http.server 8000` (đừng để cửa sổ này đóng).
2. Mở trình duyệt, ví dụ ba tư thế của trứng Khởi Đầu: `http://localhost:8000/tools/preview.html?items=Egg/Egg_Starter.glb:Hatch:0,Egg/Egg_Starter.glb:Hatch:2.4,Egg/Egg_Starter.glb:Hatch:3.1`
3. Chỉnh camera bằng các tham số, chụp màn hình khi trang đã dựng xong.

| Tham số | Ý nghĩa | Mặc định |
| --- | --- | --- |
| `items` | Danh sách `đường_dẫn_glb:tên_animation:giây`, phân cách bằng dấu phẩy (đường dẫn tính từ gốc repo) | bắt buộc |
| `orbit` | Góc nhìn, ví dụ `-25deg 78deg 16m` (góc ngang, góc đứng, khoảng cách) | `-25deg 78deg 16m` |
| `target` | Điểm camera nhìn vào, theo tọa độ glTF, ví dụ `0m 2m 0m` | `0m 2m 0m` |
| `fov` | Góc mở camera | `30deg` |
| `w`, `h` | Kích thước mỗi ô (pixel) | `300`, bằng `w` |
| `cols` | Số ô mỗi hàng | số item |

Lưu ý khi đọc ảnh:
- **File GLB quay model 180 độ quanh trục Y** (Roblox hướng -Z, glTF hướng +Z). Camera mặc định nhìn vào mặt trước của model. Tọa độ `target` theo glTF, tức là x và z của Roblox đổi dấu: một vật ở Roblox +X hiện ở bên TRÁI khi nhìn từ phía trước. Muốn nhìn từ bên hông dùng góc ngang `90deg`.
- Đừng đặt `giây` bằng đúng độ dài clip: viewer sẽ quay về khung đầu. Dùng độ dài trừ 0,1.
- GLB không có độ trong suốt, vật liệu Neon, `Beam`, hạt, script. Các part ẩn sẵn trong Roblox (`Transparency = 1`) hiện ra trong GLB trừ khi script build lọc bỏ.
- Nếu tải xong mà trang trống, mở console của trình duyệt xem lỗi (thường là mạng hoặc sai đường dẫn).
