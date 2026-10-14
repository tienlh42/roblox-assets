# Khung sản xuất: vật phẩm cầm tay hoặc công cụ có chuyển động và dây (cần câu)

Dùng khi thêm một **cây cần câu mới** hoặc một **công cụ có phần uốn cong và đầu mút di chuyển** (vợt, cần cẩu đồ chơi, roi, đũa phép có dây...). Mẫu là `FishingRod`: 6 cây dùng chung một khung, mỗi cây chỉ khác màu và phần linh thú. Quy trình 8 bước, quy ước kỹ thuật và hàm dùng lại nằm ở [PoliceGoose/PRODUCTION.md](../PoliceGoose/PRODUCTION.md), đọc trước.

Nhập vai bắt buộc (mục 1.1 của `STYLE_GUIDE.md`): vật phẩm có **linh hồn thú vật**. Mỗi cây có phần trông và cử động như thú (phao là vịt con, ống cuộn là mặt cáo, đầu cần là chân mèo...). Cây mới cần 2-3 đặc điểm hoặc cử chỉ thú, dễ thương hoặc ngố, không ghê rợn.

Phạm vi của repo: chỉ làm model, animation, phụ kiện, hiệu ứng, sound. Ai cầm cần, cần nào mở khóa thế nào, logic câu cá nằm ở phía game.

## 1. Khung dùng chung

Cần đứng thẳng, mặt trước (hướng quăng, ống cuộn, khuyên dây) là -Z, cao khoảng 6 stud. Trong `build_rod.py`:

- **`frame_parts(rod, band, grip, trim, bobber)`**: cán, ống cuộn kèm tay quay (`Crank`), ba đoạn cần (`Rod1`, `Rod2`, `Rod3`), vòng nối, khuyên dây, đầu cần (`Tip`), móc (`Hook` và các khối móc), phao (`bobber` là màu, `None` nếu phao chính là linh thú), `LineEnd` (đầu dây ở móc).
- **`JOINTS`**: `Grip` (tay cầm, cả cần xoay quanh đây khi quăng), `Rod1` → `Rod2` → `Rod3` (ba đoạn uốn cong), `Crank`, `Hook`. Tên khớp trùng tên part.
- **Dây câu** không nằm trong model: `RodEffects` tạo `Beam` từ `Tip` tới `LineEnd` nên dây tự co giãn khi móc bay ra.
- **Vị trí móc theo từng tư thế** tính bằng code: `chain_matrix`, `hook_pose(poses, mục_tiêu_thế_giới)` và `stage(grip, bends, hook, crank)`. Sửa góc cần thì móc vẫn ra đúng chỗ. Đây là phần nên dùng lại cho mọi công cụ có "đầu mút bay ra".

## 2. Hợp đồng của phần linh thú (mỗi cây)

Mỗi cây là một hàm `<ten>_decor()` trả về `(parts, joints, gestures)` và một dòng trong bảng `RODS`:

```python
RODS = {"Starter": SimpleNamespace(rarity="Common", rod=(205, 185, 95), band=WOOD_DARK, grip=(120, 80, 50), trim=WOOD, bobber=None, decor=starter_decor), ...}
```

- **`parts`**: các part linh thú (ống cuộn kiểu thú, đuôi, tai, đầu...). Part là xương phải có tên khớp.
- **`joints`**: đúng hai khớp tên `SpiritA` và `SpiritB`, mỗi khớp `(tên, cha, tâm khớp)`. Cha có thể là `Rod3` (đầu cần), `Grip` (cán và ống cuộn), `Hook` (phao) hoặc `SpiritA`. Chọn tâm khớp ở chỗ bộ phận xoay thật (cổ, gốc đuôi, mí mắt).
- **`gestures`**: **đủ tám cử chỉ** `calm`, `calmB`, `alert`, `strain`, `joy`, `joyB`, `sad`, `sadB`, mỗi cái là `{SpiritA: pose, SpiritB: pose}` (khớp không nhắc tới thì ở tư thế nghỉ). Ý nghĩa: `calm` nghỉ, `calmB` động đậy, `alert` chú ý, `strain` gồng (đang kéo), `joy` và `joyB` ăn mừng (hai pha xen kẽ), `sad` và `sadB` ỉu xìu (hụt). Dấu của góc xoay phụ thuộc cách đặt part, phải render để chỉnh.
- Mỗi cây có **2-3 đặc điểm thú**: ví dụ Cá Trê có đầu cá làm ống cuộn và râu rủ, Rùa Biển có mai, đầu và chân chèo.

## 3. Bộ animation

Game đổi attribute `Anim`: `Idle` → `Cast` → `Reel` → `Catch` hoặc `Miss` → `Idle`. Thời lượng theo mục 4.5 của `STYLE_GUIDE.md`.

| Tên | Lặp | Thời lượng (giây) | Mốc |
| --- | --- | --- | --- |
| `Idle` | có | 2,4 | Cần lắc nhẹ, móc đung đưa |
| `Cast` | không | 1,2 | Lấy đà 0,3, quất 0,6, móc rơi xuống nước **0,9**, giữ cuối |
| `Reel` | có | 1,6 | Cần cong căng, tay quay xoay một vòng, easing `Linear` |
| `Catch` | không | 1,6 | Gồng 0,3, **giật 0,5**, móc bay lên 0,8, về nghỉ |
| `Miss` | không | 1,4 | Gồng, **dây chùng 0,6**, cần rũ 0,9, lắc đầu |

Cách định nghĩa: bảng `STAGES` liệt kê từng keyframe `(giây, tâm trạng, pose cần)`. Bảng `TAKE` ánh xạ **tâm trạng** (`rest`, `wind`, `whip`, `land`, `hold`, `strain`, `jerk`, `pop`, `joy`, `slack`, `droop`, `shake`) sang một trong tám cử chỉ. `animations(gestures)` ghép pose cần với cử chỉ linh thú thành bộ animation của một cây, nên đổi cử chỉ của cây không đụng tới chuyển động của cần.

Mốc 0,9 / 0,5 / 0,6 được `RodEffects` dùng cho giọt nước và chớp sáng (`LAND_TIME`, `JERK_TIME`, `SLACK_TIME`).

## 4. Độ hiếm và hiệu ứng

| Bậc | Cây hiện có | Hiệu ứng (từ `RARITIES` trong `RodEffects`) |
| --- | --- | --- |
| Thường | Tre Khởi Đầu, Cá Trê | Viền trắng, 12 hạt khi giật cá |
| Hiếm | Rùa Biển | Viền xanh, 25 hạt, hạt lấp lánh ở đầu cần khi chờ |
| Sử thi | Cáo Tím | Viền tím, 45 hạt |
| Huyền thoại | Mèo Vàng | Viền vàng, 70 hạt |
| Thần thoại | Rồng Cầu Vồng | Viền cầu vồng, 100 hạt, dây câu cầu vồng |

Cây càng hiếm càng cầu kỳ (từ phao vịt đến đầu rồng con ngậm dây), nhưng giữ dưới khoảng 60 part. Không phải mọi cây đều phải có hiệu ứng riêng, chỉ cần đúng `Rarity`.

## 5. Cách thêm

**A. Thêm một cây mới (cùng khung):**
1. Hỏi lại: bậc độ hiếm, loài thú, hình dáng cần và ống cuộn, 2-3 đặc điểm thú, cử chỉ khi gồng, vui, buồn.
2. Viết `<ten>_decor()` trong `build_rod.py` (parts, hai khớp `SpiritA/B`, tám cử chỉ), thêm dòng vào `RODS`.
3. `python build_rod.py`, kiểm tra XML hợp lệ.
4. Render bằng `tools/preview.html`: `Idle` mặt trước, `Cast` ở 0,3 / 0,6 / 1,19, `Catch` ở 0,5, `Miss` ở 0,9 (nhìn từ bên hông, `orbit` ngang `90deg`). Kiểm tra móc không xuyên thân cần, linh thú không xuyên khuyên, cử chỉ đúng chiều.
5. Cập nhật bảng và ảnh trong `README.md`.

**B. Thêm một công cụ khác có đầu mút di chuyển (vợt, roi...):** copy `build_rod.py`, giữ ý tưởng khung: chuỗi khớp uốn, đầu mút là xương riêng, vị trí đầu mút tính bằng `hook_pose`, dây là `Beam` do script tạo. Đổi tên `Rod*`, `Hook`, `Tip`, `LineEnd` cho hợp công cụ và sửa `STAGES` theo các động tác cần có.

## 6. Checklist

- [ ] Có linh hồn thú vật (2-3 đặc điểm, đủ tám cử chỉ), dễ thương hoặc ngố
- [ ] Hai khớp `SpiritA`, `SpiritB` đúng tên, tâm khớp ở chỗ xoay thật
- [ ] Đủ năm animation `Idle`, `Cast`, `Reel`, `Catch`, `Miss`, vòng lặp khép kín (khung đầu và cuối trùng)
- [ ] Móc hạ xuống nước ở `Cast` và `Reel`, về nghỉ ở `Catch` và `Miss`
- [ ] Dưới khoảng 60 part mỗi cây
- [ ] README có bảng cây, bảng animation, cách cài, ghi rõ chưa thử trong Studio

## 7. Bẫy đã gặp

- Móc lúc nghỉ phải treo **phía trước** thân cần (`HOOK_Z`), nếu không nó nằm xuyên cần.
- File GLB không có dây câu (`Beam`), nên ảnh preview chỉ thấy móc và phao lơ lửng.
- Pose dịch chuyển của móc là trong hệ tọa độ **đã quay theo cần**; đừng đoán, dùng `hook_pose` để tính từ vị trí mục tiêu.
- Râu và dây mảnh trong GLB nhìn như que; nếu cần mềm hơn hãy chia thành vài đoạn xương.
