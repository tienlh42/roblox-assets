# Quy trình làm việc trong repo này

## Bối cảnh

Game Roblox thể loại tycoon + simulator + nhập vai, thiên về vui nhộn, đối tượng bé nam và nữ 13-17 tuổi. GDD hiện có: "Hồ Không Cho Câu" (`GDD_Ho_Khong_Cho_Cau_v2.md`, `GDD_Ho_Khong_Cho_Cau_One_Page.md`). Phong cách đã chốt ngày 2026-10-14 nằm ở [STYLE_GUIDE.md](STYLE_GUIDE.md) (hình ảnh) và [SOUND_GUIDE.md](SOUND_GUIDE.md) (âm thanh).

Model trong repo được dựng bằng script Python sinh `.rbxmx` (xem `PoliceGoose/build_police_goose.py`), từ Part có sẵn của Roblox. Các file này chưa được kiểm tra trong Studio. Model mẫu tham chiếu: `PoliceGoose/`. Cách thêm một model mới nằm ở các file `PRODUCTION.md` (mục dưới).

## Phạm vi của repo

Repo này chỉ làm **model, animation, phụ kiện, hiệu ứng và sound** của vật phẩm. Không làm system (kho đồ, thanh toán, lưu dữ liệu, logic ấp trứng, đặt đồ...). `ITEM_SYSTEM_WORKFLOW.md` chỉ là tài liệu tham khảo để bàn sau, không phải việc cần làm.

## Khung sản xuất (thêm model mới)

Mỗi folder model có một file `PRODUCTION.md`: khung sản xuất cho loại model đó (cấu trúc script, rig, bộ animation, hợp đồng đặt tên, cách thêm, checklist, bẫy đã gặp). **Khi thêm model mới, đọc file của loại gần nhất trước, rồi làm theo.** `PoliceGoose/PRODUCTION.md` còn chứa quy trình 8 bước và quy ước kỹ thuật chung cho cả repo.

| Loại model | Khung | Ví dụ |
| --- | --- | --- |
| Quái, NPC cỡ lớn có ngành nghề, nhiều animation di chuyển | [PoliceGoose/PRODUCTION.md](PoliceGoose/PRODUCTION.md) | Ngỗng cảnh sát |
| Pet chibi đi theo người chơi, mỗi pet một nghề, nở ra từ trứng | [Pet/PRODUCTION.md](Pet/PRODUCTION.md) | Mèo Đội Nồi |
| Vật thưởng nhiều bậc độ hiếm, chung bộ animation | [TreasureChest/PRODUCTION.md](TreasureChest/PRODUCTION.md) | Rương |
| Vật có vòng đời nhiều trạng thái, vỡ tách | [Egg/PRODUCTION.md](Egg/PRODUCTION.md) | Trứng |
| Vật cầm tay, công cụ có đầu mút di chuyển và dây | [FishingRod/PRODUCTION.md](FishingRod/PRODUCTION.md) | Cần câu |
| Máy, công trình cố định có ổ cắm và chỉ báo | [AutoFisher/PRODUCTION.md](AutoFisher/PRODUCTION.md) | Máy câu tự động |

Kiểm tra model trước khi giao: chạy `python -m http.server 8000` ở gốc repo rồi mở [tools/preview.html](tools/README.md) để xem các tư thế của file `.glb`. Xong thì cập nhật bảng trên nếu là loại model mới.

## Yêu cầu tạo model 3D

Khi được yêu cầu tạo model 3D (nhân vật, quái, vật phẩm, phần thưởng), luôn làm theo [STYLE_GUIDE.md](STYLE_GUIDE.md) (Chunky Cartoon vui nhộn + hiệu ứng kiểu anime) và **hỏi lại yêu cầu cụ thể trước khi làm**. Không tự suy đoán: mỗi model có yêu cầu riêng.

Các điểm cần hỏi nếu còn thiếu: vai trò, kích thước, màu chủ đạo, nét hài, độ hiếm, animation cần có.

Yếu tố nhập vai bắt buộc (mục 1.1 của `STYLE_GUIDE.md`): pet, thú, quái phải có **ngành nghề** mang tính con người (hỏi nghề gì nếu chưa rõ), vật phẩm phải có **linh hồn thú vật** (hỏi gợi ý loài thú nếu chưa rõ). Cả hai đều phải dễ thương hoặc ngố, không ghê rợn.

Animation theo thời lượng tiêu chuẩn ở mục 4.5 của `STYLE_GUIDE.md` (idle lặp 2,4 giây, sự kiện lớn như nở trứng 4-5 giây).

## Yêu cầu tạo sound

Khi được yêu cầu tạo sound (cho model, vật phẩm, phần thưởng, giao diện), luôn làm theo [SOUND_GUIDE.md](SOUND_GUIDE.md) và **hỏi lại yêu cầu cụ thể trước khi làm**. Không tự suy đoán.

1. **Đề xuất quy trình 6 bước** cho người yêu cầu, rồi hỏi các điểm còn thiếu: sự kiện nào cần sound, độ dài, lặp hay một lần, mức quan trọng (nền, hành động, cảnh báo, phần thưởng), tự tổng hợp bằng code hay dùng âm thu sẵn.
2. Các bước của quy trình:
   1. Chốt danh sách sound và phong cách (bảng sự kiện, tên file `<model>_<action>.wav`).
   2. Dựng bản nháp bằng code: `Sounds/build_sounds.py` trong thư mục model, dùng lại hàm tổng hợp của `TreasureChest/Sounds/build_sounds.py`.
   3. Người yêu cầu nghe thử và ghi feedback (giữ, chỉnh, hoặc thay).
   4. Thay bằng âm thu sẵn cho file quan trọng. Chỉ dùng nguồn cho phép dùng thương mại, ghi nguồn và license vào README của model.
   5. Upload lên Creator Hub, điền id vào bảng ở đầu script `<Model>Sounds.client.luau`.
   6. Test trong Studio: khớp animation, lặp đúng nhịp, nhiều NPC cùng lúc, có nhạc nền.
3. Số liệu bắt buộc (chi tiết ở `SOUND_GUIDE.md`): peak file 0,5, `Sound.Volume` tối đa 0,8, năng lượng chính trong 200 Hz - 2,5 kHz, không bass dưới 100 Hz, fade-out 20 ms. Sau khi sinh file thì kiểm tra lại các số này.
4. Mẫu tham chiếu: `PoliceGoose/GooseSounds.client.luau` và `PoliceGoose/Sounds/build_sounds.py`.
