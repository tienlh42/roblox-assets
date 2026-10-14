# Quy trình làm hệ thống vật phẩm (microtransaction, tương tác, trang trí)

Bản nháp để bàn sau, tổng hợp ngày 2026-10-14 từ tài liệu Roblox và DevForum. Chưa có quyết định nào được chốt. Đi cùng [STYLE_GUIDE.md](STYLE_GUIDE.md) và [SOUND_GUIDE.md](SOUND_GUIDE.md).

## 1. Phân loại vật phẩm

| Loại | Cách bán trên Roblox | Ví dụ |
| --- | --- | --- |
| Mua một lần, giữ vĩnh viễn | Game Pass | Mở khóa khu trang trí, nhân đôi tốc độ |
| Mua nhiều lần | Developer Product | Gói tiền tệ, vật phẩm tiêu hao |
| Vật phẩm tương tác | Không bán trực tiếp, bán qua pass hoặc product | Rương, pet, đồ có thể bấm |
| Vật phẩm trang trí | Như trên, kèm hệ thống đặt đồ | Nội thất, thú cưng cảnh, hiệu ứng |

## 2. Quy trình đề xuất

1. **Chốt danh mục vật phẩm:** bảng gồm tên, loại, giá Robux, độ hiếm (theo `STYLE_GUIDE.md`), cách kiếm được (mua hay chơi).
2. **Dựng model và animation** theo `STYLE_GUIDE.md`.
3. **Làm sound** theo `SOUND_GUIDE.md` và quy trình trong `CLAUDE.md`.
4. **Hệ thống tương tác:**
   - Gắn tag cho đối tượng bằng `CollectionService`.
   - Một server script nghe `ProximityPromptService.PromptTriggered`, đọc tag của đối tượng để biết phải làm gì. Cách này nhẹ hơn là mỗi vật phẩm một script riêng.
   - Đối tượng chỉ được trả về bởi `GetTagged` khi đã nằm trong workspace, nên dùng thêm `GetInstanceAddedSignal()` cho đối tượng sinh ra sau.
5. **Kho đồ và lưu dữ liệu:**
   - Lưu bằng `DataStoreService`, key theo `UserId`, chỉ server script truy cập được.
   - Không lưu Instance trực tiếp, chỉ lưu dữ liệu (id vật phẩm, số lượng).
   - Lưu khi `PlayerRemoving` và `BindToClose`, bọc `pcall`.
   - Trong Studio, quyền truy cập DataStore tắt mặc định. Chỉ bật trên bản test riêng để không ghi đè dữ liệu thật.
6. **Hệ thống trang trí (đặt đồ):**
   - Snap theo lưới (làm tròn vị trí theo bội số kích thước lưới) và raycast từ chuột, dùng pháp tuyến bề mặt để đặt đúng chỗ.
   - Mỗi món đã đặt chỉ lưu tọa độ lưới, chỉ số hướng xoay và id vật phẩm, khoảng 8 byte mỗi món nếu đóng gói gọn.
   - Server kiểm tra vị trí hợp lệ trước khi đặt, không tin client.
7. **Gắn thanh toán:**
   - Developer Product xử lý bằng `MarketplaceService.ProcessReceipt` trong script ở `ServerScriptService`. Không dùng `PromptProductPurchaseFinished` để trao thưởng, vì event này không chứng minh mua thành công.
   - Lưu mã giao dịch vào DataStore để không trao thưởng hai lần.
   - Game Pass dùng `PromptGamePassPurchaseFinished`. Event này cũng bắn khi bấm hủy nên phải kiểm tra lại quyền sở hữu phía server.
8. **Test trong Studio:** mua thử, mất mạng giữa chừng, vào lại game, nhiều người cùng lúc. Sau đó upload sound và publish.

## 3. Quy định cần lưu ý (đối tượng game là 13-17 tuổi)

Vật phẩm trả ngẫu nhiên mua bằng Robux, hoặc bằng tiền tệ trong game mà tiền đó mua bằng Robux, thuộc "Paid Random Items". Theo cập nhật cuối tháng 5/2026:

- Phải hiện tỉ lệ từng vật phẩm bằng phần trăm trước khi mua, tổng đủ 100%.
- Vật phẩm tăng may mắn hoặc cơ chế bảo hiểm cũng phải công bố số liệu, và tỉ lệ hiển thị phải đổi theo khi đang kích hoạt.
- Nếu quá nhiều kết quả thì để danh sách đầy đủ trong cửa sổ phụ, nút xem phải có chữ "Info" hoặc "Details" (biểu tượng (i) đơn lẻ là chưa đủ).
- Mọi kết quả đều phải có giá trị, không có kết quả mất trắng.
- Kiểm tra `PolicyService:GetPolicyInfoForPlayerAsync()` (khóa `ArePaidRandomItemsRestricted`) vì một số vùng bị hạn chế.
- Khai báo trong bảng câu hỏi Maturity & Compliance.

Ảnh hưởng trực tiếp tới thiết kế rương độ hiếm trong `TreasureChest/` nếu bán bằng Robux. Nên làm rõ ở bước 1.

## 4. Điểm chưa chắc, cần kiểm tra lại

- Chưa có hướng dẫn chính thức ghép cả hệ thống. Phần tương tác, kho đồ và đặt đồ chỉ có bài của cộng đồng, nhiều bài cũ (2020-2021) có code lỗi, chỉ nên làm tham khảo.
- Một bài trên DevForum nói Game Pass chưa có `ProcessReceipt` và event mua pass có thể bị giả mạo. Một bài khác nói Developer Product và Game Pass không bán được dạng tài sản bên thứ ba. Cả hai chưa được xác minh với tài liệu chính thức, cần đối chiếu lại trang `MarketplaceService` và Passes trước khi làm phần thanh toán.
- Thông tin Roblox áp dụng quy định tỉ lệ trên toàn cầu do luật Hàn Quốc chỉ đến từ một nguồn tin, cần kiểm tra trong tài liệu chính thức.

## 5. Câu hỏi cần chốt khi bàn

1. Vật phẩm bán bằng Robux là loại nào: gói tiền tệ, rương ngẫu nhiên, đồ trang trí chọn sẵn, hay pass tiện ích?
2. Có bán vật phẩm ngẫu nhiên bằng Robux hay không? Nếu có thì thiết kế hiển thị tỉ lệ từ đầu.
3. Trang trí đặt ở đâu: nhà riêng của từng người chơi, hay khu chung?
4. Bắt đầu từ đâu: bảng danh mục vật phẩm, khung script (tương tác, kho đồ, thanh toán), hay model đầu tiên?

## Nguồn

- [Developer Products](https://create.roblox.com/docs/production/monetization/developer-products)
- [Passes](https://create.roblox.com/docs/production/monetization/passes)
- [MarketplaceService](https://create.roblox.com/docs/reference/engine/classes/MarketplaceService#ProcessReceipt)
- [Paid random items policy guidelines](https://create.roblox.com/docs/production/monetization/paid-random-items)
- [Clarifying Requirements for Paid Random Items](https://devforum.roblox.com/t/clarifying-requirements-for-paid-random-items/4654622)
- [Data stores](https://create.roblox.com/docs/cloud-services/data-stores)
- [How to trigger proximityprompts in CollectionService?](https://devforum.roblox.com/t/how-to-trigger-proximityprompts-in-collectionservice/925684/34)
- [Saving player homes](https://devforum.roblox.com/t/saving-player-homes/714047)
- [Please give us ProcessReceipt for Gamepasses!](https://devforum.roblox.com/t/please-give-us-processreceipt-for-gamepasses/4613836)
