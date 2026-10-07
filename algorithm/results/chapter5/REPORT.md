# Đối chiếu Chương 5 — Simulation results

## Phần đã chạy và phần bổ sung

- Giữ nguyên cả ba kết quả V1 lần trước, không chạy lại hay ghi đè file cũ.
- Bổ sung simple/V2–V4: mỗi trường hợp 1 lần, tương ứng Bảng 5.2.
- Bổ sung A/V2–V4 và B/V2–V4: mỗi trường hợp 20 lần Monte Carlo, tương ứng Bảng 5.3–5.4.
- Tổng bổ sung: 9 trường hợp, 123 lượt GA; tổng cả kết quả cũ là 12 trường hợp, 164 lượt.

| Phiên bản | Deadline | Thời điểm chèn sạc |
|---|---|---|
| V1 | Bắt buộc | Trong đánh giá từng thế hệ |
| V2 | Mềm | Trong đánh giá từng thế hệ |
| V3 | Bắt buộc | Sau khi tìm được nghiệm cuối |
| V4 | Mềm | Sau khi tìm được nghiệm cuối |

## Bảng 5.1 — Đặc tính đội UAV

| UAV loại | m / tải trọng tối đa (kg) | Ar (m²) | Ad (m²) | vmax (m/s) | Emax (MJ) |
|---|---:|---:|---:|---:|---:|
| 0 | 1 / 1 | 0.20 | 0.4 | 16 | 0.68 |
| 1 | 2 / 2 | 0.28 | 0.6 | 19 | 0.90 |
| 2 | 3 / 3 | 0.36 | 0.8 | 20 | 1.17 |
| 3 | 4 / 4 | 0.44 | 1.0 | 22 | 1.43 |
Simple dùng UAV loại 1 và 3; complex dùng đủ 4 loại. Đã kiểm tra bằng cách đọc input
của các script, không chạy lại GA; xem `inputs.json`.

## Thông số và giới hạn đối chiếu

V2–V4 mới dùng NP=30, PC=PM=0.3, elite=5, nconv=8, epsilon=300 J, nmax=20;
FM=0.9, eta=0.8, rho=1.23, cd=0.3, cùng đặc tính UAV trong Bảng 5.1.
V1 giữ thông số repo đã chạy: elite=4, nconv=5, epsilon=100 J, nmax=15;
cd thay đổi theo UAV. Vì vậy các dòng V1 là kết quả tham khảo được tái sử dụng,
không phải thí nghiệm dùng đầy đủ cấu hình Chương 5.

Giữ nguyên 40 vị trí, ma trận đường bay, nhiệm vụ và deadline trong repo.
Luận văn mô tả deadline simple trong 0–3 giờ nhưng dữ liệu repo có giá trị tới 4.045 giờ;
luận văn cũng liệt kê khối lượng 4 kg nhưng repo chỉ tạo 0.5, 1, 2, 3 kg.
Không tự tạo lại dữ liệu ngẫu nhiên không được tài liệu công bố.
Code đã sửa so với repo gốc; lần này sửa thêm kiểm tra nhiệm vụ không khả thi khi
chèn sạc cuối, và kiểm tra lại deadline sau khi chèn sạc. Vì vậy đây là chạy bổ sung
theo bố cục/tham số thí nghiệm, không phải khẳng định tái lập chính xác số liệu luận văn.

Seed ban đầu 42 được đặt một lần trước mỗi scenario; 20 lượt dùng chuỗi ngẫu nhiên tiếp nối.
Dùng độ lệch chuẩn mẫu. Thống kê chất lượng chỉ tính trên nghiệm hợp lệ được tìm thấy;
số nghiệm / số lượt chạy được báo riêng. Không biến trường hợp không có nghiệm thành năng lượng 0.

## Bảng 5.2 — Simple scenario

| Phiên bản | Nguồn | Nghiệm | J chạy (MJ) | J luận văn (MJ) | Đúng hạn | Vòng lặp | CPU (s) | Lịch trình |
|---|---|---:|---:|---:|---:|---:|---:|---|
| V1 | Cũ, giữ lại | 1/1 | 1.625472 | 2.03 | 1.000 | 7 | 1.103 | [[1, 3, 5, 0, 4], [2]] |
| V2 | Bổ sung | 1/1 | 1.473023 | 1.85 | 1.000 | 14 | 0.862 | [[0, 4, 3], [1, 2]] |
| V3 | Bổ sung | 1/1 | 1.495107 | 2.53 | 1.000 | 9 | 0.327 | [[1, 0, 4, 6, 3], [2]] |
| V4 | Bổ sung | 1/1 | 1.488131 | 2.03 | 1.000 | 15 | 0.435 | [[1, 3, 5, 0, 4], [2]] |

## Bảng 5.3 — Complex scenario A

| Phiên bản | Nghiệm | E chạy (MJ), μ ± σ | E luận văn (MJ), μ ± σ | Đúng hạn chạy | Đúng hạn luận văn |
|---|---:|---|---|---|---|
| V1 (cũ) | 0/20 | Không có nghiệm | Không có nghiệm | Không có nghiệm | Không có nghiệm |
| V2 | 20/20 | 13.400 ± 0.554 | 15.790 ± 0.520 | 0.864 ± 0.035 | 0.857 ± 0.030 |
| V3 | 0/20 | Không có nghiệm | Không có nghiệm | Không có nghiệm | Không có nghiệm |
| V4 | 19/20 | 13.903 ± 0.709 | 16.090 ± 0.600 | 0.872 ± 0.033 | 0.879 ± 0.017 |

| Phiên bản | Trạm khác nhau, μ ± σ | Lượt ghé sạc, μ ± σ | Vòng lặp, μ ± σ | CPU/lượt (s), μ ± σ | Wall/lượt (s), μ ± σ | Wall toàn chiến dịch (s) |
|---|---|---|---|---|---|---:|
| V1 | Không có nghiệm | Không có nghiệm | Không có nghiệm | Không có nghiệm | Không có nghiệm | 44.31 |
| V2 | 3.65 ± 0.59 | 11.50 ± 0.89 | 19.60 ± 1.79 | 12.17 ± 2.57 | 12.30 ± 2.59 | 246.54 |
| V3 | Không có nghiệm | Không có nghiệm | Không có nghiệm | Không có nghiệm | Không có nghiệm | 33.39 |
| V4 | 3.74 ± 0.45 | 12.32 ± 1.06 | 18.95 ± 2.76 | 5.76 ± 2.26 | 5.87 ± 2.26 | 117.08 |

Các giá trị nchar, ni, tTOT trong luận văn:

| Phiên bản | nchar luận văn | ni luận văn | tTOT luận văn (s) |
|---|---|---|---|
| V1 | Không có nghiệm | Không có nghiệm | Không có nghiệm |
| V2 | 4.00 ± 0.00 | 8.90 ± 4.00 | 2690.20 ± 1548.80 |
| V3 | Không có nghiệm | Không có nghiệm | Không có nghiệm |
| V4 | 4.00 ± 0.00 | 9.00 ± 5.20 | 526.70 ± 340.80 |

## Bảng 5.4 — Complex scenario B

| Phiên bản | Nghiệm | E chạy (MJ), μ ± σ | E luận văn (MJ), μ ± σ | Đúng hạn chạy | Đúng hạn luận văn |
|---|---:|---|---|---|---|
| V1 (cũ) | 20/20 | 14.259 ± 0.696 | 15.060 ± 0.600 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| V2 | 20/20 | 12.592 ± 0.363 | 14.790 ± 0.460 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| V3 | 20/20 | 12.999 ± 0.678 | 15.500 ± 0.620 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| V4 | 20/20 | 12.776 ± 0.541 | 15.700 ± 0.810 | 1.000 ± 0.000 | 1.000 ± 0.000 |

| Phiên bản | Trạm khác nhau, μ ± σ | Lượt ghé sạc, μ ± σ | Vòng lặp, μ ± σ | CPU/lượt (s), μ ± σ | Wall/lượt (s), μ ± σ | Wall toàn chiến dịch (s) |
|---|---|---|---|---|---|---:|
| V1 | 3.80 ± 0.41 | 13.15 ± 0.88 | 11.90 ± 3.51 | 18.36 ± 5.18 | 18.45 ± 5.17 | 369.48 |
| V2 | 3.90 ± 0.31 | 11.25 ± 0.85 | 20.00 ± 0.00 | 12.32 ± 5.58 | 12.45 ± 5.58 | 249.38 |
| V3 | 3.90 ± 0.31 | 12.10 ± 0.79 | 19.25 ± 1.92 | 6.83 ± 1.12 | 6.93 ± 1.11 | 139.09 |
| V4 | 3.70 ± 0.47 | 11.85 ± 0.81 | 19.50 ± 1.54 | 5.25 ± 1.89 | 5.37 ± 1.90 | 107.90 |

Các giá trị nchar, ni, tTOT trong luận văn:

| Phiên bản | nchar luận văn | ni luận văn | tTOT luận văn (s) |
|---|---|---|---|
| V1 | 4.00 ± 0.00 | 7.80 ± 3.40 | 2428.80 ± 1375.30 |
| V2 | 4.00 ± 0.00 | 8.20 ± 3.20 | 2354.00 ± 1503.90 |
| V3 | 4.00 ± 0.00 | 7.40 ± 3.20 | 347.40 ± 341.20 |
| V4 | 4.00 ± 0.00 | 8.80 ± 3.60 | 373.60 ± 199.70 |

## Hình 5.1–5.3

- Môi trường simple: [Figure_5_1_environment.png](V2/Figure_5_1_environment.png).
- Lịch trình simple V2: [simple_figure_2.png](V2/simple_figure_2.png).
- Hội tụ simple V2: [simple_figure_1.png](V2/simple_figure_1.png).

