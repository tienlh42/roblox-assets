# Khung sản xuất: pet, thú, quái, NPC (và công cụ chung của repo)

Dùng khi thêm một **sinh vật cỡ lớn có ngành nghề** (quái, NPC) như `PoliceGoose`. Pet nhỏ đi theo người chơi thì dùng `Pet/PRODUCTION.md`. File này cũng chứa phần **công cụ và quy ước chung** của cả repo, các `PRODUCTION.md` khác trỏ về đây.

Trước khi làm: đọc [CLAUDE.md](../CLAUDE.md), [STYLE_GUIDE.md](../STYLE_GUIDE.md) (mục 1.1 nhập vai, 4.5 thời lượng animation, 6 checklist) và **hỏi lại yêu cầu cụ thể** của người đặt hàng.

## 1. Quy trình 8 bước cho mọi model mới

1. **Hỏi lại yêu cầu:** vai trò, nghề (pet, thú, quái) hoặc loài thú gợi ý (vật phẩm), kích thước, màu chủ đạo, nét hài, độ hiếm, các animation cần có. Với đề xuất lớn thì viết đề xuất trước, chốt rồi mới làm.
2. **Chọn khung** theo bảng dưới, tạo folder mới `<TenModel>/` (PascalCase) ở gốc repo.
3. **Viết script build** `build_<ten>.py` theo mẫu khung đã chọn, dùng lại các hàm có sẵn (mục 3), không tự viết lại bộ ghi `.rbxmx` hay `.glb`.
4. **Chạy build** (`python build_<ten>.py`), kiểm tra file `.rbxmx` là XML hợp lệ và số part hợp lý.
5. **Render xem** bằng [tools/preview.html](../tools/README.md): xem hình dáng, từng animation ở các mốc then chốt. Sửa và lặp lại tới khi ổn.
6. **Script hiệu ứng** `<Ten>Effects.client.luau` (viền sáng, hạt, ánh sáng theo `Rarity` và `Anim`), build nhúng vào `.rbxmx`.
7. **README + ảnh preview** trong folder model (thiết kế, rig, animation, hiệu ứng, cách cài, cách chỉnh, lưu ý). Sound làm sau theo quy trình sound trong `CLAUDE.md`, chỉ khi được yêu cầu.
8. **Ghi vào `CLAUDE.md`** (bảng "Khung sản xuất") nếu là một loại model mới.

| Loại model | Khung nên dùng |
| --- | --- |
| Quái, NPC cỡ lớn có ngành nghề, có thể đi lại | `PoliceGoose/` (file này) |
| Pet chibi đi theo người chơi, mỗi pet một nghề | `Pet/PRODUCTION.md` |
| Vật phẩm thưởng nhiều bậc độ hiếm, một bộ animation chung (rương) | `TreasureChest/PRODUCTION.md` |
| Vật phẩm có vòng đời nhiều trạng thái và vỡ, tách (trứng) | `Egg/PRODUCTION.md` |
| Vật phẩm cầm tay hoặc công cụ có chuyển động và dây (cần câu) | `FishingRod/PRODUCTION.md` |
| Máy, công trình đặt cố định có ổ cắm và bộ phận phụ | `AutoFisher/PRODUCTION.md` |

## 2. Quy ước kỹ thuật chung

- **Đơn vị và hướng:** stud, mặt đất `y = 0`, mặt trước của model hướng **-Z** (Roblox `LookVector`). Đầu và mắt nhìn về -Z.
- **Dựng bằng Part có sẵn**, không upload mesh hay texture. Hình dạng: `block`, `ball`, `ellipsoid` (Part cầu kèm `SpecialMesh` Sphere, kích thước tùy ý), `cylinder`, `wedge` (WedgePart).
  - `cylinder` nằm dọc trục **X** cục bộ (kích thước là chiều dài, đường kính, đường kính). Muốn dựng đứng phải xoay `rz = 90`.
  - `ball` chỉ lấy cạnh nhỏ nhất của kích thước.
  - `wedge` đầy chiều cao ở phía +Z, dốc xuống cạnh đáy ở phía -Z.
  - Màu `SILVER` tự đổi sang vật liệu `Metal`, màu còn lại `SmoothPlastic`. Vật liệu khác (Neon...) phải đặt sau khi tạo part (ví dụ hàm `set_prop` trong `Egg/build_egg.py`, `Material` Neon là `288`).
  - Vòng, ống, vòng cung không có sẵn: ghép từ nhiều khối nhỏ (ví dụ `cuff_ring` trong `build_police_goose.py`).
- **Một script build cho mỗi folder:** dữ liệu là bảng, sinh ra `.rbxmx` (Studio) và `.glb` (xem nhanh). Chỉ dùng thư viện chuẩn của Python.
- **Cấu trúc dữ liệu cốt lõi** (đủ để `export_glb.export` dùng được):
  - `PARTS`: danh sách `(tên, hình dạng, kích thước, CFrame lúc nghỉ, màu, xương)`. `xương` là tên part mà part này được hàn vào bằng `Weld`; `None` nghĩa là chính part này là xương (có khớp).
  - `JOINTS`: danh sách `(part1, part0, vị trí tâm khớp trong tọa độ thế giới lúc nghỉ)`. Mỗi cái thành một `Motor6D`. **Tên khớp phải trùng tên part con (`Part1`)**, vì animator tìm khớp theo `Part1.Name`.
  - `ANIMATIONS`: `{tên: (lặp, ưu tiên, easing, [(giây, {khớp: pose})])}`. Easing chỉ có `Linear` hoặc `Cubic`. Ưu tiên: `Idle`, `Movement`, `Action`.
  - Một pose là CFrame trong **không gian khớp, trục đồng hướng thế giới lúc nghỉ**: `rx` dương nghiêng +Y về phía +Z (ra sau), `rz` dương nghiêng +Y về phía -X, `ry` dương quay trái. Khớp không có trong pose thì về vị trí nghỉ. Không thể co giãn part bằng animation (chỉ xoay và dịch).
  - Part trang trí hàn vào **part khác không phải xương** (ví dụ một mắt xích hàn vào vòng hàn vào xương) vẫn được, cả `.rbxmx` lẫn `.glb`.
- **Attribute** do `xml_attributes` ghi vào model chỉ hỗ trợ **chuỗi** (ví dụ `Anim`, `Rarity`). Attribute số (`Progress`, `Slots`, `Fill`) không ghi sẵn, game đặt lúc chạy và script đọc `GetAttribute(...) or <mặc định>`.
- **Script client** (`RunContext = Client`) vì `Motor6D.Transform` không replicate:
  - `GooseAnimator.client.luau` (folder này) phát animation từ folder `Animations` theo attribute `Anim`, chuyển mượt 0,15 giây, animation không lặp giữ khung cuối. **Dùng lại nguyên văn** cho mọi model: script build của model khác đọc trực tiếp file này và đặt tên riêng (`ChestAnimator`, `EggAnimator`, `RodAnimator`, `MachineAnimator`).
  - Script hiệu ứng riêng của từng model đọc `Rarity` và `Anim`, chỉ dùng texture hạt có sẵn. Hạt nên gắn vào `Attachment` của part gốc không xoay, không gắn trực tiếp vào part đã bị xoay (hướng `EmissionDirection` sẽ lệch).
  - Vật chuyển động liên tục (hào quang xoay, túi lắc) do script điều khiển qua `Weld.C0` của part không nằm trong `JOINTS`, vì animator ghi đè mọi `Motor6D`.
- **Số part:** mobile nên giữ mỗi model dưới khoảng 200 part, chỉ bật hiệu ứng khi người chơi ở gần.

## 3. Hàm dùng lại (đừng viết lại)

| Cần | Dùng | Ở |
| --- | --- | --- |
| CFrame, xoay | `CF`, `cf(x, y, z, rx, ry, rz)`, `angles` | `PoliceGoose/build_police_goose.py` |
| Ghi Part, khớp, animation, model | `build_part`, `build_joint`, `build_keyframe_sequence`, `Item`, `xml_*` | như trên |
| Xuất GLB | `export(data, tên, đường dẫn)` | `PoliceGoose/export_glb.py` |
| Màu theo bảng độ hiếm, `shade` | `BLUE`, `PURPLE`, `GOLD_DARK`, `PEARL`, `RAINBOW`... | `Egg/build_egg.py` |
| Đặt Part ẩn hay Neon | `set_prop` | `Egg/build_egg.py` |
| Tinh thể, gai, vòng hào quang | `crystal`, `spike`, `ring_around` | `Egg/build_egg.py` |
| Tổng hợp sound | `sweep`, `noise`, `bell`, `honk`, `breath`, `save` | `TreasureChest/Sounds/` và `PoliceGoose/Sounds/` |

## 4. Khung cho pet, thú, quái, NPC

**Nhập vai bắt buộc:** pet, thú, quái phải có **ngành nghề** mang tính con người (mục 1.1 của `STYLE_GUIDE.md`). Nghề đọc được từ silhouette nhờ đồ nghề lớn nhất và có ít nhất một animation thể hiện công việc. Nghề vui, đời thường, không ghê rợn.

### 4.1 Xương chuẩn

Dựng theo mẫu `PoliceGoose` để script dùng lại được:

```
HumanoidRootPart (ẩn, Transparency = 1)
└─ Body ─┬─ NeckLower ─ NeckUpper ─ Head ─┬─ BeakLower (hàm dưới)
         │                                └─ LidL, LidR (mí mắt, nằm sau mắt, dịch ra trước để nhắm)
         ├─ WingL, WingR (hoặc tay)
         ├─ Tail
         ├─ LegL ─ FootL, LegR ─ FootR
         └─ <đồ nghề>  (dùi cui, còng, ...): mỗi món có khớp riêng nếu cần đung đưa
```

- Có `Humanoid`: `RigType` R15, `HipHeight` bằng chiều cao từ đáy `HumanoidRootPart` tới đất, `DisplayDistanceType` None, `RequiresNeck` false, `WalkSpeed` theo con. Nhờ vậy dùng được `Humanoid:MoveTo` và `PathfindingService`.
- Chỉ part `Body` có `CanCollide`. Đầu, cổ, chân xuyên vật cản để animation không bị vật lý đẩy lệch.
- Tên khớp và part giữ đúng quy ước trên khi có thể, để một bộ animation dùng được cho nhiều con.

### 4.2 Bộ animation

Bộ tối thiểu (tên cố định để game đổi `Anim` theo tên): `Idle`, `Walk`, `Run`, `Attack`, `Stunned`, cộng 1-2 animation thể hiện **nghề** (PoliceGoose: `Whistle`, `Threaten`). Thêm khi cần: `Alert`, `Search`, `Sleep`, `Faint`, `Fly`. Thời lượng tham khảo (theo mục 4.5 của `STYLE_GUIDE.md`):

| Animation | Lặp | Thời lượng (giây) |
| --- | --- | --- |
| `Idle` | có | 2,4 |
| `Walk` | có | 1,0 |
| `Run` | có | 0,44 |
| `Attack` | có | 0,7 |
| `Stunned` | không | 0,9 |
| `Alert`, `Whistle` | không | 1,4 và 1,0 |
| Hành động nghề dài (`Threaten`) | không | 2,4 |
| `Search`, `Sleep` | có | 2,4 và 3,0 |

Mỗi động tác chính có anticipation (nén hoặc lùi 0,1-0,2 giây) trước cú mạnh. Animation không lặp giữ khung cuối. Hàm trợ giúp như `walk_frame`, `run_frame` giúp các pha giống nhau chỉ khác thông số.

### 4.3 Sound (khi được yêu cầu)

`Sounds/build_sounds.py` dùng lại hàm tổng hợp của `TreasureChest/Sounds`, mỗi animation một file `.wav` theo quy ước `SOUND_GUIDE.md` (peak 0,5, volume tối đa 0,8, 200 Hz - 2,5 kHz, fade-out 20 ms). `<Ten>Sounds.client.luau` có bảng `SOUNDS = {tên animation = {id, volume, period}}`: animation lặp có `period` (chu kỳ phát lại), animation không lặp phát một lần. Id để trống thì im lặng.

### 4.4 Mẫu cho folder mới

```
<Ten>/
├─ build_<ten>.py            # PARTS, JOINTS, ANIMATIONS, build_model, main
├─ <Ten>Effects.client.luau  # viền sáng, hạt theo Rarity và Anim
├─ <Ten>.rbxmx, <Ten>.glb    # do script sinh ra
├─ README.md, preview.png
└─ Sounds/ (khi cần)
```

Script build khởi đầu:

```python
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "PoliceGoose"))
from build_police_goose import CF, cf, build_part, build_joint, build_keyframe_sequence, Item, xml_string, xml_attributes  # noqa: E402
from export_glb import export  # noqa: E402
```

Trong `build_model`: tạo Part, `Motor6D` cho `JOINTS`, `Weld` cho part có xương, `Humanoid`, folder `Animations`, hai script (animator dùng lại nguyên văn và script hiệu ứng riêng). Nên xem `PoliceGoose/build_police_goose.py` làm mẫu.

## 5. Checklist trước khi giao

- [ ] Đã hỏi lại yêu cầu và người đặt hàng đã chốt
- [ ] Tuân theo checklist ở mục 6 của `STYLE_GUIDE.md` (silhouette, màu, nét hài, mắt có đốm sáng, nhập vai)
- [ ] Có ngành nghề đọc được và ít nhất một animation thể hiện nghề
- [ ] Hướng -Z, đất ở `y = 0`, tên khớp trùng tên part con
- [ ] Mọi animation đã render xem ở các mốc then chốt, không có part xuyên đất hoặc xuyên nhau bất thường
- [ ] Số part hợp lý cho mobile
- [ ] README có bảng animation (tên, lặp, thời lượng, dùng khi nào), cách cài, cách chỉnh, lưu ý
- [ ] Ghi rõ **chưa mở thử trong Roblox Studio** nếu đúng như vậy

## 6. Bẫy đã gặp

- GLB quay model 180 độ: tọa độ camera trong `tools/preview.html` là tọa độ glTF (x và z đổi dấu).
- `export_glb` không biết độ trong suốt, vật liệu Neon, `Beam`, hạt: ảnh preview không thể hiện, ghi chú trong README.
- Phát animation không lặp lần hai phải đổi `Anim` sang tên khác trước.
- Animator ghi `Motor6D.Transform` mỗi khung hình: đừng điều khiển khớp đó từ script khác.
- Bản mẫu để trong `ReplicatedStorage` sẽ chạy script client trên chính bản mẫu: giữ ở `ServerStorage` rồi clone.
