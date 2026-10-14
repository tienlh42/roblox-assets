# Kế hoạch: pet lớn lên và thêm phụ kiện qua tối đa 3 dạng

**Trạng thái: kế hoạch, chưa làm.** Chốt ngày 2026-10-14 với anh Scott. Khi bắt tay làm, đọc [PRODUCTION.md](PRODUCTION.md) và hỏi lại các điểm ở mục 8.

## 1. Đã chốt

- **Tiến hóa = lớn lên về size + thêm phụ kiện.** Dùng **một model duy nhất** cho mỗi pet, không làm model riêng cho từng dạng.
- **Tối đa 3 dạng** (dạng 1 là pet vừa nở, dạng 2, dạng 3). Phụ kiện **cộng dồn**: dạng 3 có cả phụ kiện của dạng 2.
- **Cơ chế nằm ở game** (điều kiện tiến hóa, khi nào lớn, lưu dạng hiện tại, nhân bản pet, gộp pet trùng). Repo chỉ làm model, animation, phụ kiện, hiệu ứng (xem `CLAUDE.md`).
- Nhân bản pet là việc của game (`:Clone()` model từ `ServerStorage`, mỗi bản có dữ liệu riêng). Model và script hiệu ứng đã chạy độc lập từng bản sao, không cần làm thêm. Hiệu ứng nhân bản (tách đôi, lóe sáng) chưa nằm trong kế hoạch này, có thể bàn sau.

## 2. Hợp đồng giữa model và game

| Thứ | Game làm | Model làm |
| --- | --- | --- |
| Dạng hiện tại | Đặt attribute số `Stage` (1, 2 hoặc 3) trên model. Thiếu thì coi là 1 | `PetEffects` đọc `Stage`, hiện hoặc ẩn các phụ kiện theo dạng, đổi hiệu ứng theo dạng |
| Size | `pet:ScaleTo(hệ số)`, và nhân `Humanoid.HipHeight` theo hệ số. Gợi ý hệ số theo dạng: **1,0 / 1,2 / 1,4** (nhân lên trên hệ số độ hiếm đã có sẵn trong model) | Script hiệu ứng đọc size hiện tại bằng `pet:GetScale()` và tính lại kích thước hạt, vị trí hạt, bong bóng |
| Biến hình | Đặt `Anim = "Evolve"`, tween `ScaleTo` trong khoảng 1,2 đến 2,0 giây của animation, đặt `Stage` mới đúng mốc đổi hình (1,6 giây) | Animation `Evolve` (mục 5), hiệu ứng ánh sáng, và đổi phụ kiện đúng mốc 1,6 giây |

`ScaleTo` chưa được kiểm chứng với rig tự dựng này (khớp `Motor6D`, `Attachment`, hạt). **Thử trong Studio trước** bằng một pet, và nếu có gì lệch thì bàn lại cách phụ (game tự nhân kích thước, hoặc script tự đặt lại vị trí và hạt).

## 3. Quy ước phụ kiện theo dạng

- Part phụ kiện đặt tên **`Stage2_<tên>`** hoặc **`Stage3_<tên>`**, hàn vào xương tương ứng (đầu, thân, tay, đuôi, `Tool`...) để cử động theo animation.
- Trong `.rbxmx` các part này **ẩn sẵn** (`Transparency = 1`). `PetEffects` hiện khi `Stage` đủ: `Stage2_*` hiện khi `Stage >= 2`, `Stage3_*` hiện khi `Stage >= 3`.
- Mỗi dạng thêm **tối đa khoảng 12 part**. Tổng số part của pet ở dạng 3 giữ dưới khoảng 100 (hiện 39 đến 65 part).
- Phụ kiện phải **nhập vai đúng nghề** và dễ thương hoặc ngố (mục 1.1 của `STYLE_GUIDE.md`). Dạng cao hơn thì nghề "thăng chức".
- File `.glb` xem nhanh: build sinh thêm `Pet_<Tên>_Stage2.glb` và `Pet_<Tên>_Stage3.glb` có đủ phụ kiện (và nhân sẵn hệ số size) để xem ảnh, còn `Pet_<Tên>.glb` là dạng 1. Cách làm giống `AutoFisher` (GLB không ẩn được part).
- `PetEffects` thêm bảng hệ số theo độ hiếm (`size`) để cộng với `GetScale()` khi tính kích thước hạt.

## 4. Phụ kiện đề xuất cho 6 pet (nghề thăng chức theo dạng)

| Pet | Dạng 2 | Dạng 3 |
| --- | --- | --- |
| Mèo Đội Nồi (đầu bếp) | **Bếp phó:** khăn quàng đỏ, huy hiệu bếp phó trên tạp dề | **Bếp trưởng:** nắp nồi mạ vàng, huy chương bếp trưởng, vá lớn hơn |
| Chó Bánh Mì (thợ làm bánh) | **Thợ bánh giỏi:** giỏ bánh mì đeo vai, găng tay bột | **Chủ tiệm bánh:** mũ đầu bếp cao hơn gắn sao, vòng nguyệt quế, bánh mì dài mạ vàng |
| Vịt Cơ Bắp (huấn luyện viên) | **Vô địch quận:** đai vô địch ngang eo | **Vô địch thế giới:** cúp vàng đội trên đầu, tạ vàng, áo choàng |
| Mèo Ảo Thuật Gia | **Ảo thuật gia chuyên nghiệp:** bồ câu trắng đậu trên mũ, găng tay | **Phù thủy ảo thuật:** áo choàng lót sao, quả cầu pha lê bay quanh, đũa dài hơn |
| Chó K9 Cảnh Sát | **Cảnh sát trưởng:** sao cảnh sát lớn trên ngực, còi bạc | **Chỉ huy K9:** mũ gắn đại bàng, dây huân chương, còng tay vàng |
| Rồng Con Văn Phòng | **Trưởng phòng:** kính cận, thẻ nhân viên lớn | **Giám đốc:** cà vạt vàng, vương miện nhỏ, cốc cà phê |

Anh có thể đổi hoặc bổ sung nghề thăng chức khác khi chốt ở mục 8.

## 5. Animation `Evolve` (3,0 giây, không lặp)

Dùng chung cho mọi pet, giống `Hatch` của trứng (dồn nhịp, bùng nổ, hạ cánh). Mốc quan trọng cho script hiệu ứng và game:

| Giây | Việc |
| --- | --- |
| 0,0 đến 0,8 | Dồn nhịp: nén người xuống, rung, hai tay co lại, ánh sáng bắt đầu bao quanh |
| 1,2 | Bật lên cao, giơ hai tay, bắt đầu xoay |
| 1,2 đến 2,0 | Game tween `ScaleTo` lên size mới |
| **1,6** | **Mốc đổi hình:** chớp sáng, đổi phụ kiện (`Stage` mới có hiệu lực), nổ hạt |
| 2,0 đến 2,4 | Hạ cánh, nảy một lần |
| 2,4 đến 3,0 | Khoe dáng mới, vẫy tay |

Sau khi xong, game đặt `Anim` về `Idle` (hoặc `Happy` rồi `Idle`). Muốn phát lại `Evolve` thì phải đổi `Anim` sang tên khác trước (như các animation không lặp khác).

Hiệu ứng `Evolve` trong `PetEffects`: vòng sáng quanh chân từ 0,0 đến 1,6, chớp sáng và nổ hạt ở 1,6 (số hạt theo độ hiếm và dạng mới), vệt sáng rơi xuống lúc hạ cánh.

## 6. Cập nhật hiệu ứng theo dạng

- Hạt lấp lánh khi chờ tăng một mức khi lên dạng 3.
- Dạng 3 của pet **Thường, Hiếm, Sử thi** có thêm viền sáng dày hơn (hoặc một vòng hào quang nhỏ nếu anh muốn). Pet Huyền thoại và Thần thoại đã có hào quang sẵn nên chỉ tăng tốc xoay.
- `PetEffects` tính lại kích thước hạt và bong bóng theo `pet:GetScale()` mỗi lần cần phát.

## 7. Việc phải làm khi bắt đầu, theo thứ tự

1. **Vá `PetEffects`:** đọc `GetScale()`, thêm hệ số độ hiếm, ẩn hiện `Stage2_*` và `Stage3_*` theo `Stage`, tính lại hạt và bong bóng. Việc nhỏ, làm trước.
2. **Phụ kiện:** viết phụ kiện dạng 2 và 3 cho 6 pet trong `build_pet.py` (mỗi pet thêm hai danh sách part tên `Stage2_*`, `Stage3_*`), ẩn sẵn trong `.rbxmx`, và sinh thêm file GLB xem trước.
3. **Animation `Evolve`:** thêm vào bộ animation chuẩn (`animations`), thêm mốc `SWAP_TIME = 1.6` và hiệu ứng vào `PetEffects`.
4. **Render và chỉnh:** `tools/preview.html` cho ba dạng của từng pet và các mốc của `Evolve` (0,4 / 1,2 / 1,6 / 2,2).
5. **Tài liệu:** cập nhật `Pet/README.md` (bảng 3 dạng, attribute `Stage`, animation `Evolve`, hướng dẫn game) và `Pet/PRODUCTION.md` (quy ước `Stage2_*`, `Stage3_*`, mốc 1,6, mục thêm phụ kiện dạng mới).
6. **Phía game thử trong Studio:** `ScaleTo` với một pet, `HipHeight` sau khi đổi size, đổi `Stage` lúc chạy, phát `Evolve`.

## 8. Điểm cần hỏi lại anh khi làm

1. Nghề thăng chức ở mục 4 anh đã chốt chưa, hay muốn đổi?
2. Hệ số size 1,0 / 1,2 / 1,4 có hợp không, hay muốn lớn hơn (ví dụ 1,0 / 1,3 / 1,6)? (Cuối cùng do game đặt, em chỉ cần biết để kiểm tra bằng mắt khi render.)
3. Dạng 3 của pet Thường, Hiếm, Sử thi có thêm hào quang không?
4. Animation `Evolve` 3 giây có dài quá không? Có muốn bản rút gọn 2 giây cho tiến hóa liên tục không?
5. Có cần hiệu ứng nhân bản (mục 1) không, hay để game tự lo?
6. Sound cho `Evolve` làm sau theo quy trình sound.

## 9. Ngoài phạm vi (việc của game)

Điều kiện lên dạng (cấp độ, thức ăn, đủ số pet trùng), tiến độ lớn lên theo thời gian, lưu `Stage` và size của từng pet, nhân bản, gộp pet, cân bằng chỉ số theo dạng.
