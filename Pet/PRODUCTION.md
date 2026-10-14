# Khung sản xuất: pet chibi đi theo người chơi (mỗi pet có một nghề)

Dùng khi thêm **một pet mới** (hoặc một sinh vật nhỏ đi theo, có ngành nghề, có bộ animation chuẩn) như `Pet`. 6 pet dùng chung một khung chibi hai chân, mỗi pet chỉ khác loài, màu, trang phục, đồ nghề và animation nghề. Quy trình 8 bước, quy ước kỹ thuật và hàm dùng lại nằm ở [PoliceGoose/PRODUCTION.md](../PoliceGoose/PRODUCTION.md), đọc trước. Sinh vật cỡ lớn như ngỗng bảo vệ thì dùng khung ở file đó.

Nhập vai bắt buộc (mục 1.1 của `STYLE_GUIDE.md`): pet phải có **ngành nghề** mang tính con người. Nghề đọc được từ silhouette nhờ đồ nghề lớn nhất, và có animation `Job` thể hiện công việc. Nghề vui, đời thường, không ghê rợn, không nhạy cảm với lứa 13-17 tuổi.

Phạm vi của repo (xem `CLAUDE.md`): chỉ làm model, animation, phụ kiện, hiệu ứng, sound. Đi theo, tìm đường, tự chặn ngỗng, HP, tỉ lệ nở nằm ở phía game. Một trứng nở một pet: pet mới đi kèm một trứng, hãy kiểm tra `Egg/` xem trứng đã có chưa.

## 1. Khung dùng chung

Trong `build_pet.py`:

| Phần | Việc | Hàm hoặc hằng số |
| --- | --- | --- |
| Thân, đầu, tay chân, mắt, mí | Chibi cao khoảng 2,8 stud (chưa tính mũ), mắt to hai đốm sáng, má hồng, mí mắt | `frame_parts(c)`, `FRAME_JOINTS` |
| Mặt theo loài | Mèo (tai nhọn, râu, mõm nhỏ), chó (tai cụp, mõm dài, lưỡi) | `cat_face(c, ear_inner)`, `dog_face(c)` |
| Bộ animation chuẩn | `Idle`, `Walk`, `Run`, `Attack`, `Hurt`, `Exhausted`, `Happy` + `Job` | `animations(job)`, `walk_frame`, `run_frame` |
| Kích thước theo độ hiếm | Nhân kích thước, vị trí, khớp và pose theo `scale` ở cuối | `pet_data(pet)`, `scale_cf` |
| Hào quang xoay | Vòng khối Neon, script quay | `ring_around` của `Egg`, thêm bằng `ring=[màu]` |

`c` là bảng màu của pet: `fur` (lông), `belly`, `leg`, `paw` (chân, tay), `sleeve` (màu tay), `arm` (kích thước tay), `ear` (chó), `tail_tip` (mèo).

## 2. Hợp đồng của hàm pet

Mỗi pet là một hàm `<ten>()` trả về **`(parts, joints, job)`** và một dòng trong bảng `PETS`:

```python
PETS = {"CatPot": SimpleNamespace(rarity="Common", scale=1.0, build=cat_pot, ring=None), ...}
```

- **`parts`**: gồm `frame_parts(c)`, phần mặt (`cat_face`, `dog_face` hoặc viết riêng), trang phục và đồ nghề. Bone là part có `bone = None` và tên **trùng tên khớp**.
- **`joints`**: các khớp riêng của pet (tai `EarL/EarR`, `Hat`, `Tool`, cánh `WingL/WingR`, `Headband`...). Khớp chuẩn nằm ở `FRAME_JOINTS` và không cần khai lại.
- **`job`**: danh sách khung `(giây, {khớp: pose})` dài 2,4 giây, **khoảnh khắc chính ở 0,8 giây** (script hiệu ứng nổ hạt ở mốc này), khung đầu và cuối là `{}`.
- Tên quy ước: **`Tool`** là đồ nghề cầm ở tay phải (khớp `("Tool", "ArmR", vị trí bàn tay)`, các part khác hàn vào), **`Hat`** là mũ cử động, `Tail`, `EarL/EarR`. Pose nhắc tới khớp không có thì bị bỏ qua, nên một bộ animation chung dùng được cho pet thiếu tai hoặc thiếu mũ.
- Trái là **-X**, phải là **+X** (pet nhìn về -Z). Tay phải cầm đồ nghề.

## 3. Bộ animation chuẩn

| Tên | Lặp | Thời lượng (giây) | Mốc |
| --- | --- | --- | --- |
| `Idle` | có | 2,4 | Thở, chớp mắt ở 1,35 |
| `Walk` | có | 1,0 | Đi theo, mỗi nhịp chân 0,25 giây |
| `Run` | có | 0,6 | Easing `Linear`, mỗi nhịp 0,15 giây |
| `Attack` | có | 0,8 | **Húc ở 0,45** |
| `Hurt` | không | 0,7 | Bị đẩy ở 0,15 |
| `Exhausted` | không | 1,6 | Ngồi bệt ở 0,9, **bong bóng ở 0,9** |
| `Happy` | không | 1,6 | **Nhảy ở 0,5** |
| `Job` | không | 2,4 | **Khoảnh khắc chính ở 0,8** |

Các mốc này được `PetEffects` dùng (`BONK_TIME`, `HURT_TIME`, `EXHAUST_TIME`, `HAPPY_TIME`, `JOB_TIME`): đổi thì sửa cả hai nơi. Pet mới **giữ đủ 8 tên** để game dùng chung một đoạn điều khiển.

Dấu của góc xoay (cho pet nhìn về -Z, trục khớp ở gốc chi): `rx` dương đưa chi hoặc đầu về phía trước (chân, tay: +rx đưa ra trước và lên; đầu: +rx ngả ra sau), `rz` dương đưa chân tay bên phải (+X) ra ngoài (với tay trái dùng `rz` âm), tai bên phải hướng ra ngoài là `rz` âm. Luôn render để chỉnh, đừng tin vào dấu khi chưa xem ảnh.

## 4. Độ hiếm

| Bậc | Hệ số kích thước | Pet hiện có | Hiệu ứng (từ `RARITIES` trong `PetEffects`) |
| --- | --- | --- | --- |
| Thường | 1,0 | Mèo Đội Nồi, Chó Bánh Mì | Viền trắng, 8 hạt |
| Hiếm | 1,05 | Vịt Cơ Bắp | Viền xanh, 2 hạt/giây khi chờ, 14 hạt |
| Sử thi | 1,1 | Mèo Ảo Thuật Gia | Viền tím, 4 hạt/giây, 22 hạt |
| Huyền thoại | 1,15 | Chó K9 Cảnh Sát | Viền vàng, 6 hạt/giây, 32 hạt, hào quang vàng xoay |
| Thần thoại | 1,2 | Rồng Con Văn Phòng | Viền cầu vồng, 9 hạt/giây, 45 hạt, hào quang cầu vồng xoay |

Quy tắc: nhỏ nhất là Thường. Pet càng hiếm càng cầu kỳ (đồ nghề, màu, hào quang) nhưng vẫn giữ dưới khoảng 80 part.

## 5. Cách thêm một pet mới

1. **Hỏi lại:** loài (ưu tiên chó mèo và loài được yêu thích), nghề và đồ nghề lớn nhất, bậc độ hiếm, trứng nở ra nó, màu, nét hài, động tác `Job` (khoảnh khắc chính).
2. Viết hàm `<ten>()` trong `build_pet.py`: bảng màu `c`, `frame_parts(c)`, mặt (dùng lại `cat_face`/`dog_face` hoặc viết riêng, nhớ đủ `Tail`), trang phục, `Tool` và `Hat`, các khớp riêng, khung `Job`. Thêm một dòng vào `PETS`.
3. `python build_pet.py`, kiểm tra XML hợp lệ.
4. Render bằng `tools/preview.html`: `Idle` mặt trước và nghiêng, `Job` ở 0,4 và 0,8, `Attack` ở 0,45, `Exhausted` ở 1,5, `Happy` ở 0,5. Chỉnh tới khi đồ nghề không xuyên đầu hoặc thân, và tay cầm đúng chỗ.
5. Cập nhật bảng, ảnh trong `README.md`, và nếu có trứng mới thì cột "Pet gợi ý" trong `Egg/README.md`.

## 6. Checklist

- [ ] Có ngành nghề đọc được từ silhouette (đồ nghề lớn nhất) và `Job` thể hiện công việc
- [ ] Loài và đồ nghề dễ thương hoặc ngố, không ghê rợn, không nhạy cảm
- [ ] Đủ 8 animation chuẩn; mốc 0,45 / 0,9 / 0,5 / 0,8 khớp script hiệu ứng
- [ ] Mắt có đốm sáng, mí mắt nhắm được; có `Tail`
- [ ] `Humanoid` R15, `HipHeight` đúng, chỉ `Body` có `CanCollide`
- [ ] Hệ số kích thước theo độ hiếm; hào quang xoay nếu là Huyền thoại hoặc Thần thoại
- [ ] Dưới khoảng 80 part
- [ ] README ghi rõ chưa mở thử trong Studio (nếu đúng như vậy)

## 7. Bẫy đã gặp

- Hào quang đặt quá cao sẽ cắt ngang mặt pet: đặt thấp (khoảng ngang bụng) và nghiêng sao cho phía trước thấp hơn phía sau.
- Mí mắt là một ellipsoid **nằm sau** mắt, dịch ra trước để nhắm; đặt nó ra trước mắt từ đầu thì mắt biến mất.
- Chân gắn vào `HumanoidRootPart` (không gắn vào `Body`) nên khi thân nhún hoặc nhảy, chân đứng yên trên đất.
- Đồ nghề cầm tay phải hàn vào khớp `Tool` có tâm ở bàn tay: pose xoay `Tool` quay quanh bàn tay chứ không quanh vai.
- GLB không thể hiện hạt, bong bóng, Neon, `Humanoid`: ghi chú trong README.
