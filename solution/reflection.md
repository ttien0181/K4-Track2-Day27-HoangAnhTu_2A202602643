# Thu hoạch Data Siege

Họ tên: Hoàng Anh Tú. MSSV: 2A202602643.

Khó nhất là các lỗi có độ lệch nhỏ, nhất là khi từng chỉ số của một batch vẫn nằm trong ngưỡng lịch sử. Vì vậy, bên cạnh các điều kiện riêng cho số hàng, tỷ lệ thiếu customer ID, giá trị đơn hàng và độ trễ, em dùng thêm khoảng cách tổng hợp của bốn chỉ số. Cách này bắt thêm lỗi trên Public mà không tạo báo động giả trong các lần chạy Practice và Public. Feature drift cũng khó vì ngưỡng 3 sigma trong baseline thấp hơn một số dao động bình thường được mô tả trong đề; em dùng ngưỡng tách riêng để hạn chế báo động nhầm.

Em gọi đúng một công cụ đo lường cho mỗi sự kiện. Kết quả Practice đạt 50,00 điểm, TPR 1,0000, FPR 0 và chi phí 180/220 credits. Public đạt 46,90 điểm, TPR 0,9744, FPR 0 và chi phí 240/220 credits. Em chấp nhận vượt 20 credits ở Public vì kiểm tra đầy đủ các luồng có lợi hơn việc bỏ qua sự kiện để tiết kiệm chi phí. Private đạt 32,41 điểm, TPR 0,6481, FPR 0 và không vượt ngân sách. Kết quả Private cho thấy nhiều lỗi tinh vi vẫn chưa được phát hiện.

Nếu có thêm thời gian, em sẽ dùng `ctx.state` để lưu thống kê của các sự kiện trước đó theo từng loại dữ liệu, chẳng hạn trung bình động và độ phân tán. Em sẽ cập nhật thống kê thận trọng để một batch bất thường không làm lệch mốc tham chiếu. Sau đó, em sẽ so sánh mức cải thiện TPR với mức tăng FPR trên dữ liệu kiểm thử được phép dùng, thay vì chỉ hạ mọi ngưỡng cảnh báo.
