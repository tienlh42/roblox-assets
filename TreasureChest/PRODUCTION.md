# Khung sản xuất: vật phẩm thưởng nhiều bậc độ hiếm, dùng chung một bộ animation

Dùng khi thêm một **vật chứa hoặc vật thưởng có 5 bậc độ hiếm**, mỗi bậc khác hình dáng và màu nhưng cùng một rig và cùng bộ animation (rương, hộp quà, túi báu, bình...). Mẫu là `TreasureChest`. Quy trình 8 bước, quy ước kỹ thuật và hàm dùng lại nằm ở [PoliceGoose/PRODUCTION.md](../PoliceGoose/PRODUCTION.md), đọc trước.

Nhập vai bắt buộc (mục 1.1 của `STYLE_GUIDE.md`): vật phẩm có **linh hồn thú vật**. Rương là một con thú ham ăn: mắt to có đốm sáng, miệng có răng, thè lưỡi khi mở, bậc Thần thoại có cánh. Vật mới cần 2-3 đặc điểm hoặc cử chỉ thú tương tự.

## 1. Cấu trúc folder và script

```
<Ten>/
├─ build_<ten>.py            # TIERS, <ten>_data(tier), ANIMATIONS, build_model, main
├─ <Ten>Effects.client.luau
├─ <Ten>Sounds.client.luau   # khi làm sound
├─ Sounds/build_sounds.py    # khi làm sound
├─ <Ten>_Common|Rare|Epic|Legendary|Mythic .rbxmx / .glb
└─ README.md, preview.png
```

`build_treasure_chest.py` là mẫu:

- **`TIERS`**: bảng số liệu và màu cho từng bậc (`scale`, `body`, `trim`, `metal`, `iris`, số đá quý, kiểu trang trí bên hông). Muốn đổi vẻ ngoài một bậc thì sửa ở đây.
- **`chest_data(tier)`** trả về `SimpleNamespace(PARTS, JOINTS, ANIMATIONS)`. Bên trong là các hàm nhỏ nhân kích thước theo `scale` (`part`, `placed`, `mirrored` cho cặp trái phải), cộng các hàm hình học riêng (`arch` vòm ghép từ tấm phẳng, `end_cap`, `ring`, `gem` kim cương nhiều mặt).
- **`build_model(tier, data)`** và **`main()`** lặp qua mọi bậc, ghi `Model` tên `<Ten>_<Rarity>`, attribute `Anim` (mặc định `Idle`) và `Rarity`.
- Bậc đặc biệt nằm trong khối `if tier == "Epic" / "Legendary" / "Mythic"` ở cuối `chest_data` (thêm kim cương, vương miện, mây, cánh).

## 2. Rig và quy ước đặt tên

```
HumanoidRootPart (neo cố định, ẩn)
└─ Base ─┬─ Lid        (nắp vòm, bản lề ở phía sau; mắt, răng, đai... đi theo nắp)
         ├─ Tongue     (lưỡi, nằm phẳng trong thân khi đóng)
         ├─ WingL, WingR (chỉ bậc Thần thoại; bậc khác bỏ qua phần cánh trong pose)
```

- Không có `Humanoid`: server tự đặt vị trí bằng `PivotTo` hoặc tween.
- Vật mới giữ nguyên tên `Base` (thân cố định so với đất) và đặt phần chuyển động (nắp, cửa, lưỡi...) thành xương con. Có thể đổi tên xương động nhưng phải sửa pose, script hiệu ứng và sound cho khớp.
- Mỗi bậc khoảng 135-210 part. Bậc càng hiếm càng nhiều part, nhưng đừng vượt khoảng 220.

## 3. Bộ animation chuẩn

| Tên | Lặp | Thời lượng (giây) | Mốc quan trọng |
| --- | --- | --- | --- |
| `Spawn` | không | 1,2 | Nổi lên từ nước, nảy, đáp xuống |
| `Idle` | có | 1,4 | Rung báo hiệu, nắp hé nhẹ |
| `Open` | không | 1,4 | Nén xuống, **bật nắp ở 0,42**, thè lưỡi lắc, giữ tư thế mở |
| `Vanish` | không | 1,1 | Đóng nắp **sập ở 0,25**, nhảy lên, xoay, chìm xuống nước |

Pose `Idle` và `Open` có anticipation (nén xuống trước khi bật). Mốc 0,42 và 0,25 được script hiệu ứng và sound dùng đúng (hằng số `LID_POP_TIME`, mốc 0,25), nên đổi mốc là phải sửa cả script lẫn sound. Vật mới giữ đủ bốn tên này để game dùng chung một đoạn điều khiển (`Spawn` → `Idle` → `Open` → `Vanish`).

## 4. Phân biệt độ hiếm

Phải nhận ra bậc ngay cả khi nhìn bóng:

| Bậc | Cao (stud) | Cách nhận ra |
| --- | --- | --- |
| Thường (`Common`) | 2,6 | Nhỏ nhất, ít chi tiết, màu gốc |
| Hiếm (`Rare`) | 2,8 | Thêm một màu nhấn (đai xanh), nhiều đá hơn |
| Sử thi (`Epic`) | 3,2 | Đổi màu thân, đá lớn trên nắp |
| Huyền thoại (`Legendary`) | 3,6 | Vàng, vương miện, tia sáng khi mở |
| Thần thoại (`Mythic`) | 4,0 | Cánh, mây, đá cầu vồng, hiệu ứng cầu vồng |

Quy tắc: kích thước tăng dần, số chi tiết tăng dần, màu bám bảng độ hiếm ở mục 2 của `STYLE_GUIDE.md`, hiệu ứng nặng dần (tia sáng chỉ từ Huyền thoại).

## 5. Script hiệu ứng

`ChestEffects.client.luau` là mẫu: bảng `RARITIES = {color, idleRate, burst, rays, rainbow}` cho 5 bậc, `Highlight` viền theo màu bậc (nhấp nháy khi `Idle`, Thần thoại đổi màu cầu vồng), hạt lấp lánh khi chờ (từ Hiếm), bắn hạt và chớp sáng đúng mốc `Open`, tia sáng `Neon` bắn lên từ Huyền thoại, bọt nước khi `Spawn`, mờ dần khi `Vanish`. Bậc lạ (Rarity không có trong bảng) thì `assert` báo lỗi.

## 6. Sound (khi được yêu cầu)

`Sounds/build_sounds.py` tổng hợp 9 file: `spawn`, `idle`, `open`, `vanish` và 5 tiếng chuông `chime_<bậc>`. Chuông dùng thang ngũ cung C5-C6, bậc càng hiếm càng nhiều nốt (1, 2, 3, 4, 6) và đuôi vang dài hơn. `ChestSounds.client.luau` có bảng `IDS` (id để trống thì im lặng) và phát đúng mốc 0,42 giây của `Open` cho chuông. Đây cũng là nơi chứa **hàm tổng hợp dùng chung cho cả repo** (`sweep`, `noise`, `bell`, `save`...), sửa ở đây thì mọi model dùng chung thay đổi theo.

## 7. Cách thêm

**A. Thêm hoặc sửa một bậc của vật có sẵn:** sửa `TIERS` (số liệu, màu) và khối `if tier == ...` (chi tiết riêng), thêm dòng bậc vào bảng `RARITIES` của script hiệu ứng nếu là bậc mới, chạy `python build_treasure_chest.py`.

**B. Thêm một vật thưởng mới có 5 bậc (ví dụ hộp quà):**
1. Hỏi lại yêu cầu: hình dạng, phần động (nắp, cửa, lò xo), linh hồn thú, 5 bậc khác nhau thế nào.
2. Tạo folder `<Ten>/`, copy `build_treasure_chest.py` thành `build_<ten>.py`, đổi tên model và file.
3. Viết lại `TIERS` và `<ten>_data(tier)` (giữ khung `part`/`placed`/`mirrored`). Giữ xương `Base`, đặt tên xương động rõ ràng.
4. Giữ bốn animation `Spawn`, `Idle`, `Open`, `Vanish` với mốc thời gian tương tự; chỉnh pose theo phần động của vật.
5. Copy `ChestEffects.client.luau` thành `<Ten>Effects.client.luau`, sửa tên part gốc (`base`), mốc thời gian và bảng bậc nếu cần.
6. Build, render bằng `tools/preview.html` ở `Idle`, `Open` (0,42 và 1,0), `Vanish`, kiểm tra cả 5 bậc.
7. Viết README theo mẫu `TreasureChest/README.md` (thiết kế, bảng 5 bậc, rig, animation, hiệu ứng, cách cài, cách chỉnh, lưu ý).

## 8. Checklist

- [ ] Có linh hồn thú vật (2-3 đặc điểm hoặc cử chỉ) mà vẫn nhận ra là đồ vật, không ghê rợn
- [ ] 5 bậc nhận ra bằng bóng, càng hiếm càng to và nhiều chi tiết
- [ ] Đủ `Spawn`, `Idle`, `Open`, `Vanish`; mốc 0,42 và 0,25 khớp script hiệu ứng và sound
- [ ] Mỗi bậc dưới khoảng 220 part
- [ ] Đã render cả 5 bậc ở ba trạng thái (chờ, đang mở, mở xong)
- [ ] README ghi rõ chưa mở thử trong Studio (nếu đúng như vậy)

## 9. Bẫy đã gặp

- Mắt nằm trên mặt trước của nắp nên khi nắp mở quay lên trời, chỉ còn ló ra mép nắp. Cân nhắc khi chọn vị trí mặt.
- Roblox không đổi kích thước part bằng animation nên `Vanish` là chìm và xoay chứ không thu nhỏ.
- Part Roblox không có vân gỗ, đinh tán, bóng vẽ tay: muốn mịn hơn thì dựng mesh ngoài rồi upload.
