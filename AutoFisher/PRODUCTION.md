# Khung sản xuất: máy, công trình đặt cố định có ổ cắm và bộ phận phụ (máy câu tự động)

Dùng khi thêm một **máy hoặc công trình đặt cố định** có chỗ cắm đồ (cần câu, bình, ống...) và có chỉ báo trạng thái (đèn, túi chứa). Mẫu là `AutoFisher`: một con bồ nông làm bằng máy móc, 5 lớp màu theo độ hiếm. Quy trình 8 bước, quy ước kỹ thuật và hàm dùng lại nằm ở [PoliceGoose/PRODUCTION.md](../PoliceGoose/PRODUCTION.md), đọc trước.

Nhập vai bắt buộc (mục 1.1 của `STYLE_GUIDE.md`): máy là vật phẩm nên có **linh hồn thú vật**: ở đây cả cái máy là một con thú (bồ nông), túi dưới mỏ chứa cá cho thấy máy còn trống hay đã đầy. Máy mới cần một con thú hợp chức năng và một **chỉ báo trạng thái đọc được bằng mắt**, không cần giao diện.

Phạm vi của repo: chỉ làm model, animation, phụ kiện, hiệu ứng, sound. Logic tự câu (bao lâu có cá, cá gì), mở ổ, thay cần nằm ở phía game.

## 1. Khung dùng chung

Trong `build_machine.py`:

- **`pelican_parts(c)`**: bệ, thân, bụng, bánh răng, đèn (`Lamp`), ống khói, đai, cánh, đuôi, cổ, đầu, mỏ, túi (`Pouch`, ba mức `PouchBulge1-3` ẩn sẵn), mí mắt, mũ. `c` là bảng màu của một lớp.
- **`rod_parts(i, slot)`**: một ổ cắm (`Socket<i>`, `SocketRim<i>`), cần tre hai đoạn, móc và phao, nắp đậy và ổ khóa (`LockCap<i>`, `LockBody<i>`, ẩn sẵn). Tất cả part cần mang tiền tố `Rod<i>_`.
- **`SLOTS`**: vị trí và độ nghiêng của ba ổ (cần giữa trên lưng, hai cần ở hai vai chĩa ra mặt nước). `slot_frame` cho khung tọa độ của một cần.
- **Chu kỳ quăng kéo của cần**: bảng `CYCLE` (mỗi 0,4 giây của vòng 2,4 giây: độ uốn hai đoạn, tầm xa, độ cao móc). `rod_pose(i, ...)` tính tư thế ba khớp của một cần và đặt móc bằng phép tính ngược (`axis_rotation`, `swing`, `rod_chain`). Ba cần chạy lệch pha 0,8 giây (`rods_working`).
- **`RARITIES`**: màu từng lớp (`body`, `belly`, `bands`, `head`, `wing_tip`, `hat`, `platform`) và hàm phụ kiện thêm (`extras`).
- **`HIDDEN_AT_START`**: tiền tố tên các part ẩn sẵn trong Studio (`LockCap`, `LockBody`, `PouchBulge`). GLB không ẩn được part nên script build **lọc chúng ra khỏi file `.glb`**.

## 2. Rig và attribute

```
HumanoidRootPart
└─ Body ─┬─ Gear, WingL, WingR, Tail
         ├─ Neck ─ Head ─┬─ Jaw ─ Pouch
         │               └─ LidL, LidR
         └─ Rod<i>_A ─ Rod<i>_B ─ Rod<i>_Hook   (i = 1, 2, 3)
```

| Attribute | Ý nghĩa | Mặc định |
| --- | --- | --- |
| `Anim` | Trạng thái animation | `Idle` |
| `Rarity` | Bậc độ hiếm, ghi sẵn theo file | theo file |
| `Slots` | Số ổ đang mở (1-3): ổ chưa mở hiện nắp và khóa, cần và dây của ổ ẩn đi | 3 khi thiếu |
| `Fill` | Số cá trong túi (0-3): hiện `PouchBulge1` đến `PouchBulge3` | 0 khi thiếu |

`Slots` và `Fill` là attribute số nên không ghi sẵn, `MachineEffects` đọc `GetAttribute(...) or <mặc định>`.

## 3. Bộ animation

| Tên | Lặp | Thời lượng (giây) | Mốc |
| --- | --- | --- | --- |
| `Idle` | có | 2,4 | Gật gù, mắt lim dim, cần buông, đèn vàng |
| `Work` | có | 2,4 | Thân rung, bánh răng quay một vòng, ba cần tự quăng và kéo (easing `Linear`), đèn xanh lá |
| `Catch` | không | 1,2 | Ngẩng đầu, há mỏ 0,25, **nuốt 0,5**, cúi lại nhìn nước |
| `Full` | có | 2,4 | Mỏ há chờ lấy, cánh vẫy luân phiên, đèn đỏ chớp |
| `Collect` | không | 1,6 | Ngả đầu, nhắm mắt 0,35, **nhả cá 0,6**, **hắt xì 1,4** |

Mốc 0,5 / 0,6 / 1,4 được `MachineEffects` dùng (`GULP_TIME`, `SPIT_TIME`, `SNEEZE_TIME`): đổi thời lượng thì sửa cả hai nơi. Máy mới giữ **năm tên này** để game dùng chung một đoạn điều khiển.

## 4. Độ hiếm và hiệu ứng

| Bậc | Màu và phụ kiện thêm | Hiệu ứng (từ `RARITIES` trong `MachineEffects`) |
| --- | --- | --- |
| Thường | Thùng gỗ, đai bạc, mũ vàng | Viền trắng, 15 hạt khi nuốt cá |
| Hiếm | Thân xanh biển, đai đồng thau, vỏ sò trên bệ | Viền xanh, 30 hạt, hạt lấp lánh khi chờ và làm việc |
| Sử thi | Thân tím, tinh thể ở bốn góc bệ | Viền tím, 50 hạt |
| Huyền thoại | Thân vàng, hào quang vàng xoay | Viền vàng, 80 hạt |
| Thần thoại | Thân ngọc trai, đai cầu vồng, sừng vàng, hào quang cầu vồng xoay | Viền cầu vồng, 110 hạt, dây câu cầu vồng |

Hiệu ứng chung: đèn trạng thái (vàng `Idle`, xanh lá `Work`, trắng xanh `Catch`, đỏ chớp `Full`, xanh biển `Collect`), hơi nước từ ống khói (thưa, đều, một cụm lớn khi hắt xì), ba `Beam` dây câu, giọt hạt ở miệng khi nuốt và nhả.

## 5. Cách thêm

**A. Thêm một lớp độ hiếm hoặc đổi màu:** thêm một dòng vào `RARITIES` (màu + hàm `extras`), chạy `python build_machine.py`. Muốn bậc mới, thêm cả dòng vào bảng `RARITIES` của `MachineEffects`.

**B. Thêm một loại máy khác (con thú khác, chức năng khác):**
1. Hỏi lại: chức năng, con thú, chỉ báo "đầy", số ổ cắm, bộ phận cắm vào.
2. Copy `build_machine.py`, viết `<thu>_parts(c)` thay cho `pelican_parts`, giữ `Lamp` và chỉ báo chứa (mức `Bulge` hoặc tương đương) để `MachineEffects` dùng lại.
3. Giữ năm trạng thái `Idle`, `Work`, `Catch`, `Full`, `Collect`; viết lại pose cho con thú mới (xem `ANIMATIONS`).
4. Giữ quy ước tên: `Rod<i>_*`, `Socket<i>`, `LockCap<i>`, `LockBody<i>`, `PouchBulge<n>`, `Halo`. Đổi tên hợp lý thì sửa luôn `MachineEffects` (`slotOf`, `updateSlots`, `updateFill`).
5. Build, render bằng `tools/preview.html` (mặt trước, nghiêng 60 độ và bên hông 90 độ) ở `Idle`, `Work` (0,4), `Catch` (0,25 và 0,5), `Full` (0,6), `Collect` (0,6).
6. README: thiết kế, 5 lớp, rig, animation, bảng attribute, hiệu ứng, cách thay cần, lưu ý.

## 6. Thay cần tre bằng FishingRod

Ba cần tre là phần của máy (các part `Rod1_*` đến `Rod3_*`) để máy chạy ngay. Khi game dùng model `FishingRod`: ẩn các part `Rod<i>_*`, gắn model cần vào ổ theo bảng `SLOTS` (cần giữa ở khoảng (0, 3,05, 1,0) nghiêng 20 độ về phía trước, hai cần vai ở khoảng (±1,15, 2,95, 0) nghiêng 55 độ ra ngoài và về phía trước). `Socket<i>` và `SocketRim<i>` (ống cắm) ở lại.

## 7. Checklist

- [ ] Có linh hồn thú vật và nét hài, không ghê rợn; chỉ báo trạng thái đọc được bằng mắt
- [ ] Đủ năm animation, `Work` khép kín ở 2,4 giây, ba cần lệch pha
- [ ] Part ẩn sẵn đặt tên theo quy ước và được lọc khỏi `.glb`
- [ ] Đèn, `Slots`, `Fill` hoạt động theo attribute (đọc script, vì chưa chạy thử được ngoài Studio)
- [ ] Số part dưới khoảng 130 mỗi lớp (cộng ba cần)
- [ ] README ghi rõ chưa mở thử trong Studio (nếu đúng như vậy)

## 8. Bẫy đã gặp

- Cần ở giữa nằm cạnh mũ bảo hộ và cổ: chọn độ nghiêng sao cho móc treo không chạm đầu.
- Đầu và mỏ dựng lần đầu quá nhỏ so với thân nên không ra "bồ nông": mỏ dài và túi to là nhận diện chính, đừng thu nhỏ.
- Cần nghiêng ra ngoài bị uốn theo trục **ngang vuông góc hướng nghiêng của cần**, không phải trục X của thế giới: dùng `swing(i, độ)`.
- GLB không có dây, ổ khóa, mức túi phồng, Neon: ảnh preview chỉ thể hiện phần còn lại.
