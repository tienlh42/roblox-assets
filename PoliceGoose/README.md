# Ngỗng bảo vệ (PoliceGoose)

Model và animation cho kẻ canh gác đầu tiên trong GDD *Hồ Không Cho Câu*.

![preview](preview.png)

## Thiết kế

- **Phong cách:** hoạt hình 3D ít chi tiết, dựng hoàn toàn từ Part có sẵn của Roblox (khối, cầu, trụ, nêm và SpecialMesh dạng cầu). Không cần upload mesh hay texture.
- **Nhận diện từ xa:** cổ trắng dài, thân mặc đồng phục xanh navy, mũ kê-pi có huy hiệu vàng, mỏ cam ngậm còi bạc. Nhìn bóng là biết "ngỗng bảo vệ".
- **Đồ nghề:** dùi cui đen đầu bạc cầm ở mép trước cánh phải, còng tay bạc móc bên hông trái thắt lưng. Còng tay có khớp riêng nên đung đưa khi đi, chạy hoặc khi ngỗng lắc để dọa.
- **Chi tiết hài:** lông mày cau có, thắt lưng có khóa vàng, huy hiệu trên ngực.
- **Kích thước:** cao khoảng 6,7 stud tính cả mũ, cao hơn nhân vật người chơi một chút để trông có uy.

| Màu | Dùng cho |
| --- | --- |
| Navy `#1F3A68` | Thân (áo đồng phục), cánh (tay áo) |
| Trắng `#F5F5F0` | Cổ, đầu, đuôi, đầu cánh |
| Cam `#FF8C1A` | Mỏ, chân |
| Vàng `#F2C230` | Huy hiệu, khóa thắt lưng |
| Đen / bạc | Dùi cui, còng tay, còi |

### Rig

```
HumanoidRootPart
└─ Body
   ├─ NeckLower ─ NeckUpper ─ Head ─┬─ BeakLower
   │                                └─ LidL, LidR   (mí mắt, nhắm khi ngủ hoặc ngất)
   ├─ WingL
   ├─ WingR ─ Baton                         (dùi cui)
   ├─ Tail
   ├─ LegL ─ FootL
   ├─ LegR ─ FootR
   └─ Cuffs                                 (còng tay)
```

Mỗi khớp là một `Motor6D`, tên khớp trùng với tên part con. Các part trang trí như mũ, mắt, còi, huy hiệu và các mắt xích còng tay được hàn bằng `Weld` vào part xương tương ứng. Có `Humanoid` (R15, `HipHeight` 1,6) nên dùng được `Humanoid:MoveTo` và tuần tra bằng `PathfindingService`.

## Animation

| Tên | Lặp | Dùng khi (theo GDD) |
| --- | --- | --- |
| `Idle` | có | Đứng gác, ngó quanh |
| `Walk` | có | Đi chậm khi tuần tra theo mốc |
| `Run` | có | Đuổi người chơi |
| `Fly` | có | Bay vỗ cánh (chỉ là hình ảnh, xem phần lưu ý) |
| `Attack` | có | Mổ hoặc cắn pet đang chặn |
| `Sleep` | có | Ngủ gật khi trực (bảo vệ ngủ gật hoặc đổi ca) |
| `Faint` | không | Ngất xỉu rồi nằm im, giữ tư thế cuối |
| `Alert` | không | Dựng cổ khi nghi ngờ, giữ tư thế cuối |
| `Whistle` | không | Thổi còi trước khi đuổi |
| `Stunned` | không | Khựng lại khi trúng đòn của pet |
| `Search` | có | Cúi tìm ở vị trí mất dấu cuối cùng |
| `Threaten` | không | Đứng ở ranh giới nơi an toàn, chĩa dùi cui gõ dọa rồi lắc còng tay |

## Cài vào Roblox Studio

1. Kéo thả `PoliceGoose.rbxmx` vào cửa sổ Studio, hoặc chuột phải vào `ServerStorage` rồi chọn **Insert from File...**
2. Để thử nhanh, đặt model vào `Workspace` và bấm **Play** (F5). Trong Explorer (đang ở góc nhìn client), chọn `PoliceGoose` rồi đổi attribute `Anim` trong Properties sang tên animation muốn xem.
3. Khi chạy game thật, giữ bản mẫu trong `ServerStorage` và clone ra `Workspace`. Đừng để bản mẫu trong `ReplicatedStorage`, vì script client sẽ chạy cả trên bản mẫu đó.

## Đổi animation từ server

Animation được phát trên client bởi script `GooseAnimator` (`RunContext = Client`). Server chỉ cần đổi attribute `Anim` trên model:

```lua
local goose = ServerStorage.PoliceGoose:Clone()
goose.Parent = workspace
goose.HumanoidRootPart:SetNetworkOwner(nil)

goose:SetAttribute("Anim", "Walk")
goose.Humanoid.WalkSpeed = 10
goose.Humanoid:MoveTo(patrolPoint)

-- Phát hiện người chơi
goose:SetAttribute("Anim", "Alert")
task.wait(1.4)
goose:SetAttribute("Anim", "Whistle")
task.wait(1)
goose:SetAttribute("Anim", "Run")
goose.Humanoid.WalkSpeed = 18
```

- Animation không lặp sẽ giữ khung cuối cho tới khi server đổi `Anim` sang tên khác. Muốn phát lại cùng một animation không lặp (ví dụ `Stunned` hai lần liên tiếp) thì phải đổi `Anim` sang tên khác trước, rồi mới đặt lại tên cũ.
- Khi đổi animation, script tự chuyển mượt trong 0,15 giây.
- Tên animation sai sẽ báo lỗi `PoliceGoose: unknown animation ...` trong Output.

## Xem nhanh bằng file GLB

`PoliceGoose.glb` chứa cùng model và 12 animation (mỗi animation là một clip, đặt tên giống bảng trên). Mở bằng:

- Trình duyệt: kéo file vào https://gltf-viewer.donmccurdy.com và chọn clip trong mục Animation.
- Windows: ứng dụng **3D Viewer**.
- Blender: **File > Import > glTF 2.0**, chọn clip trong Action Editor hoặc NLA.

File GLB chỉ dùng để xem. Muốn đưa vào Roblox thì dùng `PoliceGoose.rbxmx`.

## Chỉnh sửa

- **Chỉnh dáng hoặc animation bằng code:** sửa `build_police_goose.py` (bảng `PARTS`, `JOINTS`, `ANIMATIONS`), chạy `python build_police_goose.py` để tạo lại file `.rbxmx`. Script chỉ dùng thư viện chuẩn của Python.
- **Xuất lại GLB:** chạy `python export_glb.py` (chỉ dùng thư viện chuẩn).
- **Chỉnh animation trong Studio:** các `KeyframeSequence` nằm trong thư mục `Animations` của model. Sửa trực tiếp `Pose.CFrame` hoặc thay bằng bản mới là script tự đọc lại, không cần upload.
- **Muốn dùng `Animator` chuẩn của Roblox:** publish từng `KeyframeSequence` để lấy Animation ID (chuột phải, chọn **Save to Roblox**, hoặc dùng Animation Editor), rồi `LoadAnimation` như rig thường. Khi đó bỏ script `GooseAnimator` đi để hai cơ chế không cùng ghi vào `Motor6D.Transform`.

## Lưu ý

- `Fly` chỉ nâng thân và vỗ cánh. Ngỗng không tự bay lên: `Humanoid` vẫn giữ nó trên mặt đất. Nếu cần bay thật, phải tự di chuyển `HumanoidRootPart` (ví dụ bằng `AlignPosition`).
- Chỉ part `Body` có `CanCollide`. Đầu, cổ và chân xuyên qua vật cản để animation mổ hay ngất không bị vật lý đẩy lệch.
- Âm thanh như còi hay tiếng kêu "quác" chưa có. Có thể phát `Sound` từ server cùng lúc đổi `Anim`.
- File được sinh bằng script và đã kiểm tra hình dáng, tư thế bằng ảnh render offline (`preview.png`), nhưng **chưa mở thử trong Roblox Studio**.
