# CE339 — N06 / E2 requirements

Source: `DeTai_BTL_CE339_2026.xlsx`; all 7 sheets inspected.
Workbook SHA-256: `92550fa524dec3e2ffb768b6cd9b7f439e35bebd61bfab82a052fe625b44a24f`.

This file preserves the relevant workbook text. Suggested roles are not assignments.

## Course component

Source: HuongDan!A1:A2.

CE339 – CÔNG NGHỆ IoT VÀ ỨNG DỤNG · BÀI TẬP LỚN (ĐỒ ÁN NHÓM) HK1 2026–2027

Thành phần đánh giá A2 (15%). Phương án gọn: mọi đề tài xoay quanh 1 board ESP32 + linh kiện phổ thông. GV: ThS. Nguyễn Duy Xuân Bách – bachndx@uit.edu.vn

## Group registration

Source: DangKy!A31:I33.

| Member | Student ID | Email | Assigned role |
| --- | --- | --- | --- |
| Trần Minh Nhật | 23521100 | 23521100@gm.uit.edu.vn | Not assigned |
| Nguyễn Tiến Đạt | 23520263 | 23520263@gm.uit.edu.vn | Not assigned |
| Lê Nguyễn Thành Danh | 23520241 | 23520241@gm.uit.edu.vn | Not assigned |

Registered context: Giám sát rung động quạt/động cơ, chẩn đoán bằng cây quyết định trên ESP32.
Git repository: not entered.
Wokwi link: not entered.

## Topic E2

### Tên đề tài

Source: DeTai!B6.

Giám sát rung động quạt/động cơ, chẩn đoán bằng cây quyết định trên ESP32

### Bài toán

Source: DeTai!C6.

Quạt hoặc động cơ nhỏ khi mất cân bằng hay lỏng chân đế sẽ rung khác thường. Cần nút cảm biến tự nhận biết trạng thái và chỉ báo lên khi có thay đổi.

### Linh kiện (đều có trong Wokwi)

Source: DeTai!D6.

ESP32 · MPU6050 (gia tốc) · LED 3 màu (trạng thái) · nút nhấn (chọn chế độ mô phỏng) · (tuỳ chọn) OLED

### Yêu cầu BẮT BUỘC (≤ 7 điểm)

Source: DeTai!E6.

1. Đọc MPU6050 ở 200–1000 Hz; mỗi giây tính RMS, peak, crest factor ngay trên ESP32.
2. Wokwi không có rung thật: sinh tín hiệu rung mô phỏng trong code cho 3 trạng thái (bình thường / mất cân bằng / lỏng), chọn bằng nút nhấn.
3. Huấn luyện cây quyết định độ sâu ≤ 3 trên tập dữ liệu GV cung cấp (dữ liệu Lab TH5, chỉ dùng các cột RMS và peak – đúng các đặc trưng ESP32 tự tính được); tín hiệu mô phỏng trên ESP32 phải có biên độ cùng cỡ với dữ liệu này.
4. Chuyển cây thành các lệnh if–else bằng C, chạy trên ESP32, hiển thị trạng thái bằng LED.
5. Gửi đặc trưng và trạng thái qua MQTT; dashboard.

### MỞ RỘNG (8–9 điểm)

Source: DeTai!F6.

• Chỉ gửi khi trạng thái thay đổi + gửi định kỳ thưa → tính % lưu lượng giảm so với gửi dữ liệu thô
• So sánh chia dữ liệu ngẫu nhiên và chia theo thời gian, confusion matrix

### NÂNG CAO (tuỳ chọn, 10 điểm)

Source: DeTai!G6.

• Thay cây bằng MLP nhỏ lượng tử hoá int8 (dùng lại TH6)
• Thêm đặc trưng tần số bằng FFT

### Thành phần AI (mức vừa sức)

Source: DeTai!H6.

Bắt buộc: cây quyết định huấn luyện bằng scikit-learn rồi chạy trên ESP32 dưới dạng if–else (Ch.10). Nâng cao: MLP int8 (Ch.11).

### Chỉ tiêu đo tối thiểu

Source: DeTai!I6.

• Kết quả cây trên ESP32 trùng 100% với Python trên bộ vector kiểm thử
• Báo cáo F1 khi chia theo thời gian, so với mô hình "luôn trả lời bình thường"
• Lưu lượng gửi giảm ≥ 10 lần so với gửi thô

### Sản phẩm nộp

Source: DeTai!J6.

Link Wokwi + mã · notebook huấn luyện · bảng đối chiếu ESP32 vs Python · báo cáo

### Kiến thức môn áp dụng (chương)

Source: DeTai!K6.

Ch.3 tần số lấy mẫu · Ch.7 MQTT · Ch.9 đặc trưng thời gian · Ch.10 cây quyết định, đánh giá · Ch.11 suy luận trên MCU

### Dùng lại Lab

Source: DeTai!L6.

TH1, TH3, TH5, TH6

### Kiến thức tự tìm hiểu thêm

Source: DeTai!M6.

Xuất cây quyết định sklearn sang mã C (export_text) · Crest factor · (Nâng cao) arduinoFFT

### Phân vai gợi ý (3 SV)

Source: DeTai!N6.

SV1 Firmware đọc IMU + đặc trưng · SV2 Huấn luyện cây + chuyển sang C · SV3 MQTT + dashboard + đo lưu lượng

## E2 component list

Source: LinhKien, E2 column.

| Component | Wokwi part | Requirement |
| --- | --- | --- |
| ESP32 DevKit | `board-esp32-devkit-c-v4` | Required |
| MPU6050 – gia tốc | `wokwi-mpu6050` | Required |
| LED | `wokwi-led` | Required |
| Nút nhấn | `wokwi-pushbutton` | Required |
| Màn hình OLED SSD1306 | `board-ssd1306` | Optional |

## Applicable course rules

Source: HuongDan!A5:B16.

### Mục tiêu

Nhóm SV làm một sản phẩm IoT nhỏ chạy được đầu–cuối trên ESP32: đọc cảm biến → xử lý trên board → gửi MQTT → dashboard → điều khiển ngược lại, có một thành phần AI đơn giản và biết đo đạc, đánh giá bằng con số.

### Thiết bị

Chỉ cần 1 ESP32 và các linh kiện phổ thông (cảm biến nhiệt ẩm, biến trở, nút nhấn, LED, relay, cảm biến chuyển động…). Tất cả đều có trong Wokwi nên làm được hoàn toàn trên Wokwi, không bắt buộc mua thiết bị. Nhóm có ESP32 thật và chạy lại được trên phần cứng: cộng tối đa 0,5 điểm.

### Giới hạn Wokwi cần biết

Không có Bluetooth; mạng miễn phí (Public Gateway) chỉ ra Internet, không nhận kết nối vào → không chạy web server trên ESP32, ESP32 chỉ nói chuyện qua broker MQTT công cộng; ADC và MPU6050 không có nhiễu/rung thật (sinh tín hiệu bằng code); nút nhấn có mô phỏng dội phím. Chi tiết: 00_QuyDinhThucHanh_2026.docx trong ThucHanh_2026.

### Backend / dashboard

Không bắt buộc tự viết backend. Được dùng nền tảng có sẵn: Node-RED, ThingsBoard, ThingSpeak, hoặc backend Python của Lab TH4.

### Ba cấp yêu cầu

Mỗi đề chia 3 cấp: Bắt buộc (đủ và đạt chỉ tiêu → tối đa 7 điểm), Mở rộng (8–9 điểm), Nâng cao (tuỳ chọn, để đạt 10). Nhóm tự chọn làm tới cấp nào.

### Dùng lại Lab

Các đề được thiết kế để dùng lại kết quả 6 bài thực hành (TH1 lọc số, TH2 FreeRTOS, TH3 MQTT, TH4 backend, TH5 học máy, TH6 suy luận int8). Cột "Dùng lại Lab" ghi rõ bài nào.

### Quy mô nhóm

2–3 sinh viên/nhóm. Mỗi đề tài tối đa 5 nhóm; các nhóm cùng đề phải khác nhau ở bối cảnh hoặc phần mở rộng (ghi khi đăng ký).

### Quy định dùng AI

Vùng XANH: được dùng AI sinh mã, nhưng phải ghi rõ phần AI sinh trong README, nộp "nhật ký AI", và mỗi thành viên giải thích, sửa được tại chỗ phần mình phụ trách.

### Điểm cá nhân

Điểm cá nhân = Điểm nhóm × Hệ số vấn đáp (1,0 / 0,8 / 0,5 / 0,2). Lịch sử commit Git là căn cứ xác định đóng góp.

### Mốc nộp

Mốc 1 – Tuần 7 (30%); Mốc 2 – Tuần 11 (30%); Mốc 3 – Tuần 14–15 (40%). Xem sheet MocNopBai và Rubric.

### Sản phẩm chung

• Link dự án Wokwi + mã nguồn (kho Git, README) • Ảnh/video dashboard • Bảng số liệu đo (CSV) • Báo cáo PDF • Video demo 3–5 phút • Slide bảo vệ

### Topic MQTT

Trên broker công cộng, mọi topic phải bắt đầu bằng ce339/<MaNhom>/… để không đụng nhóm khác.

## Submission milestones

Source: MocNopBai!A5:F8.

### Đăng ký — Tuần 2 (0%)

Chọn đề, lập nhóm 2–3 SV, phân vai; ghi bối cảnh riêng nếu trùng đề

Submission: Sheet DangKy

Assessment: GV duyệt, cân đối số nhóm/đề

### Mốc 1 — Tuần 7 (30%)

Sơ đồ khối hệ thống; sơ đồ nối dây trên Wokwi; cây topic MQTT; luồng giám sát và luồng điều khiển; bảng chỉ tiêu cần đạt; ESP32 đã đọc được cảm biến

Submission: Báo cáo ngắn 4–6 trang + link Wokwi bản đầu

Assessment: Trình bày 5 phút/nhóm

### Mốc 2 — Tuần 11 (30%)

Hoàn thành cấp Bắt buộc phần thiết bị–MQTT–dashboard chạy đầu–cuối; có số liệu đo (chu kỳ gửi, độ trễ lệnh); đã có dữ liệu cho phần AI

Submission: Link Wokwi, mã nguồn, CSV số liệu, video ngắn

Assessment: Demo + vấn đáp từng thành viên

### Mốc 3 — Tuần 14–15 (40%)

Hoàn thành phần AI và các cấp Mở rộng/Nâng cao đã chọn; đo đạc theo chỉ tiêu; phân tích hạn chế

Submission: Báo cáo cuối, slide, video 3–5 phút, nhật ký AI

Assessment: Bảo vệ trước lớp + vấn đáp cá nhân

## Grading

Source: Rubric!A5:D14; D18/F18 contain the score formulas.

- Chưa đạt Bắt buộc: maximum 5. Thiếu một hoặc nhiều mục Bắt buộc, hoặc hệ thống không chạy đầu–cuối. Chấm theo phần đã chạy được
- Bắt buộc: maximum 7. Đủ mọi mục Bắt buộc, chạy đầu–cuối, có thành phần AI bắt buộc, đạt chỉ tiêu đo. Mức chuẩn của đồ án
- Mở rộng: maximum 9. Đạt cấp Bắt buộc + hoàn thành các mục Mở rộng, có số liệu đo minh chứng. 8 điểm nếu làm được một phần Mở rộng
- Nâng cao: maximum 10. Đạt cấp Mở rộng + ít nhất một mục Nâng cao hoạt động và được đánh giá.

Individual score = (M1 × 0.30 + M2 × 0.30 + M3 × 0.40) × oral-assessment factor.

The workbook rounds the weighted group score and then the individual score to two decimal places.

- 1: Giải thích đúng và sửa được mã tại chỗ khi GV thay đổi yêu cầu
- 0.8: Giải thích đúng nhưng không sửa được tại chỗ
- 0.5: Giải thích được một phần
- 0.2: Không giải thích được phần do mình nộp

## E2 chapter matrix

Source: MaTran_Chuong!A6:Q6.

- Ch.2 Nhúng/RTOS: also used.
- Ch.3 Thế giới thực: core.
- Ch.7 Giao thức: core.
- Ch.8 Backend: also used.
- Ch.9 Chuỗi thời gian: core.
- Ch.10 Học máy: core.
- Ch.11 TinyML: also used.
