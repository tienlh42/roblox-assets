# Khung sản xuất: vật phẩm có vòng đời nhiều trạng thái và vỡ tách (trứng)

Dùng khi thêm một **quả trứng mới** hoặc một **vật phẩm vỡ làm đôi rồi lộ vật bên trong** (vỏ sò, quả cầu, bình...). Mẫu là `Egg`: 6 quả dùng chung một khung, mỗi quả chỉ khác màu, họa tiết, phụ kiện. Quy trình 8 bước, quy ước kỹ thuật và hàm dùng lại nằm ở [PoliceGoose/PRODUCTION.md](../PoliceGoose/PRODUCTION.md), đọc trước.

Nhập vai bắt buộc (mục 1.1 của `STYLE_GUIDE.md`): vật phẩm có **linh hồn thú vật**. Trứng mang đặc điểm của pet bên trong (ví dụ ếch ngồi lên đòi ở chung, cá bơi trong ô cửa, túi cá của rồng). Quả mới cần 2-3 đặc điểm hoặc cử chỉ thú. Ngôi sao mặt cười là vật nhảy ra, dùng chung cho mọi quả.

Phạm vi của repo (xem `CLAUDE.md`): chỉ làm model, animation, phụ kiện, hiệu ứng, sound. Logic ấp (thời gian, ai ấp, pet nhận được) nằm ở phía game.

## 1. Khung dùng chung

Trong `build_egg.py`:

| Phần | Việc | Hàm hoặc hằng số |
| --- | --- | --- |
| Hình trứng | Cao 3 stud, rộng 2,3 stud, mặt cắt ở `CUT = 1.5` | `egg_radius(y)`, `RADIUS`, `CUT` |
| Vỏ hai nửa | Lát cầu dẹt chồng nhau cho mặt cong, hai dải trụ quanh mặt cắt để mặt cắt phẳng | `shell_slices`, `cylinder_band`, `LOWER_BAND`, `UPPER_BAND` |
| Đường vỡ răng cưa | 20 tấm vuông xoay 45 độ xen kẽ (nửa dưới nhô lên, nửa trên thòng xuống), ghép kín khi đóng | `tooth_parts(color)`, `TEETH` |
| Vết nứt 3 mức | Chuỗi khối nhỏ, ẩn sẵn | `crack_parts`, `CRACKS` |
| Ngôi sao mặt cười | 5 cánh bầu bĩnh và mặt, ẩn trong nửa dưới | `star_parts`, `STAR_CENTER` |
| Điểm trên mặt vỏ | Khung gắn lên bề mặt theo góc và độ cao | `surface_frame(phi, y, inset)`, `half_of(y)` |
| Họa tiết dùng lại | Đốm, vòng xoắn, hàng mảnh (vảy, tinh thể), tinh thể, gai, hào quang | `dots`, `swirl`, `plate_rows`, `crystal`, `spike`, `ring_around` |

Hệ trục: `phi = 0` là mặt trước (-Z), dương về phía bên phải của người nhìn. Đừng đặt họa tiết vào **vùng mặt cắt** (khoảng `y` từ 1,25 đến 1,75), nơi có răng cưa.

## 2. Rig

```
HumanoidRootPart
└─ Base (nửa vỏ dưới)
   ├─ Top (nửa vỏ trên) ─ Topper (phụ kiện đỉnh)
   └─ Star (ngôi sao, ẩn trong Base)
```

`Topper` là tên **bắt buộc** của xương phụ kiện đỉnh (nắp nồi, cụm cỏ, ống thở, tinh thể, lông vũ, gai). Animation rung và hất lên của nó dùng chung cho mọi quả. Part phụ kiện khác hàn vào `Topper`.

## 3. Ba trạng thái và mốc thời gian

Game đổi attribute `Anim`. Thời lượng theo mục 4.5 của `STYLE_GUIDE.md`.

| Tên | Lặp | Thời lượng (giây) | Mốc |
| --- | --- | --- | --- |
| `Idle` | có | 2,4 | Nằm yên, lắc nhẹ |
| `Incubate` | có | 2,4 | Rung chậm, phụ kiện đỉnh lạch cạch, vỏ phồng nhẹ |
| `Hatch` | không | 5,0 | Lắc tăng dần (0 đến 2,0, vết nứt hiện ở **0,4 / 0,9 / 1,4**), nén xuống 2,0, vỏ nhún lên 2,2, **vỡ đôi 2,4**, nửa trên chạm đất **3,4**, ngôi sao ổn định **3,8**, kết thúc 5,0 |

Script hiệu ứng dùng đúng các mốc này (`CRACK_TIMES`, `POP_TIME`, `LAND_TIME`, `SETTLE_TIME`): đổi thời lượng thì phải sửa cả hai nơi. Muốn đổi cách vỡ (ví dụ nhiều mảnh) thì sửa pose `Top` và có thể thêm xương mới.

## 4. Hợp đồng của hàm trang trí (mỗi quả)

Mỗi quả là một hàm `<ten>_decor()` trả về **danh sách part** `(tên, hình dạng, kích thước, CFrame, màu, xương)` và một dòng trong bảng `EGGS`:

```python
EGGS = {"Starter": SimpleNamespace(rarity="Common", shell=WHITE, lining=(255, 205, 140), decor=starter_decor), ...}
```

- `shell`: màu vỏ và răng cưa. `lining`: màu mặt cắt phẳng bên trong. `rarity`: ghi vào attribute `Rarity` (`Common`, `Rare`, `Epic`, `Legendary`, `Mythic`).
- Part trên nửa trên (y > `CUT`) có xương `Top`, nửa dưới có `Base`, phụ kiện đỉnh có `Topper` (`half_of(y)` giúp chọn).
- Xương phụ kiện đỉnh là một part tên đúng `Topper`, `bone = None`, các part khác hàn vào nó.
- **Tên part có ý nghĩa với script:** `Crack<mức>_<n>` (vết nứt, ẩn sẵn), `Halo` và `HaloRing<n>` (hào quang xoay, vòng khối Neon), `BagHinge` (vật lắc lư, ví dụ túi). Hai kiểu sau do `EggEffects` điều khiển qua `Weld.C0`.
- Họa tiết bám bề mặt đặt bằng `surface_frame` để quay đúng pháp tuyến. Phụ kiện treo hay nổi đặt bằng `cf` trực tiếp.

## 5. Phân biệt độ hiếm

| Bậc | Quả hiện có | Hiệu ứng (từ `RARITIES` trong `EggEffects`) |
| --- | --- | --- |
| Thường | Khởi Đầu, Lau Sậy | Viền trắng, 20 hạt khi vỡ |
| Hiếm | Bong Bóng | Viền xanh, 40 hạt, hạt lấp lánh khi chờ |
| Sử thi | Tinh Thể | Viền tím, 70 hạt |
| Huyền thoại | Vàng Mồi | Viền vàng, 110 hạt, tia sáng khi vỡ, hào quang xoay |
| Thần thoại | Rồng | Viền cầu vồng, 150 hạt, tia sáng, hào quang cầu vồng xoay, túi lắc lư |

Quả càng hiếm càng nhiều chi tiết và hiệu ứng (Gold 183 part, Dragon 158 part, Starter 90 part). Nếu thêm quả mới cùng bậc, chọn họa tiết và phụ kiện khác loại với quả cùng bậc có sẵn.

## 6. Script hiệu ứng và attribute

`EggEffects.client.luau` dùng chung cho mọi quả, đọc `Rarity`, `Anim`, `Progress`:

- `Progress` (số 0 đến 1) do game đặt khi ấp: hiện vết nứt mức 1 ở 0,3, mức 2 ở 0,6, mức 3 ở 0,9. Thiếu thì coi là 0.
- Hạt gắn vào `Attachment` của `HumanoidRootPart` (giữa, trên đỉnh, sát đất) nên hướng bay luôn đúng; ngôi sao có vệt hạt riêng.
- Hào quang xoay và túi lắc chỉ chạy khi model có part `Halo` hay `BagHinge`.

## 7. Cách thêm

**A. Thêm một quả mới (cùng khung):**
1. Hỏi lại: bậc độ hiếm, pet bên trong, hình dáng, màu, phụ kiện đỉnh, nét hài, 2-3 đặc điểm thú.
2. Viết `<ten>_decor()` trong `build_egg.py` (dùng các hàm họa tiết ở mục 1), thêm dòng vào `EGGS`.
3. `python build_egg.py` (sinh cả 6 file, có thể chỉ xem quả mới), kiểm tra XML hợp lệ.
4. Render bằng `tools/preview.html` ở `Idle` (mặt trước và nghiêng), `Hatch` ở 0, 2,4, 3,1 và 4,9 (đừng dùng 5,0). Chỉnh tới khi họa tiết không xuyên nhau và phụ kiện không lọt vào vỏ.
5. Cập nhật bảng và ảnh trong `README.md`.

**B. Thêm một vật vỡ đôi khác (không phải trứng):** copy `build_egg.py`, thay `egg_radius` bằng profile của vật (hộp, vỏ sò...), thay vỏ và đường vỡ cho hợp hình, giữ nguyên xương `Base`, `Top`, `Topper`, `Star` và ba trạng thái, giữ các mốc thời gian hoặc sửa đồng bộ trong script hiệu ứng.

## 8. Checklist

- [ ] Có linh hồn thú vật (2-3 đặc điểm) và nét hài, không ghê rợn
- [ ] Họa tiết không đè lên vùng mặt cắt, không xuyên vỏ
- [ ] Phụ kiện đỉnh tên đúng `Topper`; part ẩn (vết nứt, hub hào quang) đặt tên theo quy ước
- [ ] Đã render `Idle` và bốn mốc của `Hatch`, nửa vỏ không lún xuống đất khi nằm xuống
- [ ] Số part hợp lý cho mobile (dưới khoảng 200)
- [ ] README có bảng animation, mốc thời gian, cách cài, lưu ý chưa thử trong Studio

## 9. Bẫy đã gặp

- Hạt gắn vào part đã xoay (ví dụ trụ xoay 90 độ) thì hướng `Top` lệch sang bên: luôn gắn vào `Attachment` của root.
- Vòng khối quay quanh trục của chính nó thì không thấy gì: quay quanh trục đứng (`CFrame.Angles(0, t, 0) * C0`) để vòng nghiêng nhìn thấy chuyển động.
- Khung hình cuối `Hatch` đúng bằng độ dài clip sẽ quay về đầu trong trình xem: dùng 4,9.
- Mặt cắt phẳng cần dải trụ (cầu dẹt chỉ cho mặt cong, đỉnh sẽ nhọn).
