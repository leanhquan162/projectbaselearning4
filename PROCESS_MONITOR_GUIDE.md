# Process Monitor (pmon) - Hướng Dẫn Sử Dụng

## Giới Thiệu
Process Monitor là công cụ giám sát tiến trình tích hợp trong MiniShell, cung cấp giao diện TUI (Text User Interface) để theo dõi và quản lý các tiến trình hệ thống.

## Khởi Động
Từ MiniShell prompt, gõ lệnh:
```bash
MiniShell> pmon
```

## Các Tính Năng Mới

### 1. Hiển Thị Thông Tin Chi Tiết

#### Thông Tin Được Hiển Thị:
- **PID**: Process ID
- **USER**: Người dùng sở hữu tiến trình
- **%CPU**: Phần trăm CPU đang sử dụng
- **%MEM**: Phần trăm Memory đang sử dụng
- **STATUS**: Trạng thái tiến trình (Run, Sleep, Stop, etc.)
- **RUNTIME**: Thời gian chạy của tiến trình (MM:SS, HH:MM:SS, hoặc DDdHH:MM)
- **THR**: Số lượng threads (luồng)
- **I/O R**: Số byte đã đọc từ disk
- **I/O W**: Số byte đã ghi vào disk
- **COMMAND**: Tên lệnh/tiến trình

#### Mã Màu:
- 🟢 **Màu xanh lá**: Sử dụng tài nguyên bình thường (< 50%)
- 🟡 **Màu vàng**: Sử dụng tài nguyên trung bình (50-80%)
- 🔴 **Màu đỏ**: Sử dụng tài nguyên cao (> 80%)

### 2. Điều Hướng và Phân Trang

#### Phím Điều Hướng:
- `↑` / `↓`: Di chuyển lên/xuống để chọn tiến trình
- `PgUp`: Chuyển đến trang trước
- `PgDn`: Chuyển đến trang tiếp theo

#### Thông Tin Phân Trang:
- Hiển thị ở cuối màn hình
- Format: `Page X/Y | Total: N processes | Selected: M/N`
- Mỗi trang hiển thị tối đa 15 tiến trình

### 3. Lọc Tiến Trình

#### Lọc Theo Tên (phím `/`):
1. Nhấn phím `/`
2. Nhập substring của tên tiến trình (ví dụ: "python")
3. Nhấn `Enter` để áp dụng
4. Nhấn `ESC` để hủy

**Ví dụ:**
- Nhập "python" → Hiển thị tất cả tiến trình có tên chứa "python"
- Nhập "chrom" → Hiển thị Chrome và các tiến trình liên quan

#### Lọc Theo CPU (phím `c`):
1. Nhấn phím `c`
2. Nhập ngưỡng CPU tối thiểu (ví dụ: "10" cho 10%)
3. Nhấn `Enter` để áp dụng

**Ví dụ:**
- Nhập "10" → Chỉ hiển thị tiến trình dùng ≥ 10% CPU
- Nhập "50" → Chỉ hiển thị tiến trình dùng ≥ 50% CPU

#### Lọc Theo Memory (phím `m`):
1. Nhấn phím `m`
2. Nhập ngưỡng Memory tối thiểu (ví dụ: "20" cho 20%)
3. Nhấn `Enter` để áp dụng

**Ví dụ:**
- Nhập "20" → Chỉ hiển thị tiến trình dùng ≥ 20% Memory
- Nhập "5" → Chỉ hiển thị tiến trình dùng ≥ 5% Memory

#### Kết Hợp Nhiều Bộ Lọc:
Bạn có thể kết hợp các bộ lọc:
- Lọc theo tên + CPU
- Lọc theo tên + Memory
- Lọc theo CPU + Memory
- Lọc theo tất cả 3 (tên + CPU + Memory)

**Ví dụ:**
1. Nhấn `/`, nhập "python", Enter
2. Nhấn `c`, nhập "10", Enter
→ Kết quả: Chỉ hiển thị tiến trình Python dùng ≥ 10% CPU

#### Reset Bộ Lọc (phím `r`):
- Nhấn `r` để xóa tất cả bộ lọc
- Quay lại hiển thị tất cả tiến trình

### 4. Gửi Tín Hiệu Đến Tiến Trình

#### Chọn Tiến Trình:
1. Dùng phím `↑` / `↓` để di chuyển
2. Tiến trình được chọn sẽ được highlight màu xanh dương

#### Các Tín Hiệu Có Thể Gửi:

**`k` - SIGKILL:**
- Kill tiến trình ngay lập tức
- Không thể bỏ qua hoặc xử lý
- Dùng cho tiến trình không phản hồi
- ⚠️ Cẩn thận: Có thể làm mất dữ liệu chưa lưu

**`t` - SIGTERM:**
- Yêu cầu tiến trình kết thúc gracefully
- Tiến trình có cơ hội dọn dẹp và lưu dữ liệu
- Nên thử trước khi dùng SIGKILL

**`s` - SIGSTOP:**
- Tạm dừng tiến trình
- Tiến trình không còn chạy nhưng vẫn trong memory
- Dùng để giải phóng CPU tạm thời

**`C` - SIGCONT (Shift+C):**
- Tiếp tục tiến trình đã bị tạm dừng
- Dùng sau khi đã gửi SIGSTOP

#### Xác Nhận:
- Sau khi nhấn phím tín hiệu, một hộp thoại xuất hiện
- Nhấn `y` để xác nhận gửi tín hiệu
- Nhấn phím khác để hủy
- Kết quả được hiển thị (thành công hoặc lỗi)

### 5. Điều Chỉnh Thời Gian Refresh

#### Thay Đổi Refresh Interval:
- `+` hoặc `=`: Tăng 0.5 giây (tối đa 10 giây)
- `-` hoặc `_`: Giảm 0.5 giây (tối thiểu 0.5 giây)

#### Thông Tin Hiển Thị:
- Hiện tại: "Refresh: X.Xs (+/- to adjust)"
- Giá trị mặc định: 1.5 giây

#### Khuyến Nghị:
- **Hệ thống mạnh**: 0.5-1.5 giây (cập nhật nhanh)
- **Hệ thống trung bình**: 1.5-2.5 giây (cân bằng)
- **Hệ thống yếu**: 3.0-5.0 giây (giảm tải)

### 6. Help và Thoát

#### Xem Help (phím `h`):
- Hiển thị màn hình trợ giúp đầy đủ
- Liệt kê tất cả phím tắt
- Nhấn phím bất kỳ để quay lại

#### Thoát (phím `q`):
- Thoát Process Monitor
- Quay lại MiniShell prompt

## Tổng Hợp Phím Tắt

### Điều Hướng
| Phím | Chức Năng |
|------|-----------|
| `↑` | Di chuyển lên |
| `↓` | Di chuyển xuống |
| `PgUp` | Trang trước |
| `PgDn` | Trang sau |

### Lọc và Tìm Kiếm
| Phím | Chức Năng |
|------|-----------|
| `/` | Lọc theo tên tiến trình |
| `c` | Lọc theo CPU threshold |
| `m` | Lọc theo Memory threshold |
| `r` | Reset tất cả bộ lọc |

### Gửi Tín Hiệu
| Phím | Tín Hiệu | Mô Tả |
|------|----------|-------|
| `k` | SIGKILL | Kill ngay lập tức |
| `t` | SIGTERM | Kết thúc gracefully |
| `s` | SIGSTOP | Tạm dừng |
| `C` | SIGCONT | Tiếp tục |

### Hiển Thị
| Phím | Chức Năng |
|------|-----------|
| `+` / `=` | Tăng refresh interval |
| `-` / `_` | Giảm refresh interval |

### Khác
| Phím | Chức Năng |
|------|-----------|
| `h` | Hiển thị help |
| `q` | Thoát |

## Ví Dụ Thực Hành

### Ví Dụ 1: Tìm Và Kill Tiến Trình Chrome Đang Treo
```
1. Khởi động pmon: pmon
2. Nhấn /
3. Nhập: chrome
4. Nhấn Enter
5. Dùng ↑/↓ để chọn tiến trình Chrome cần kill
6. Nhấn k (SIGKILL)
7. Nhấn y để xác nhận
```

### Ví Dụ 2: Giám Sát Tiến Trình Dùng CPU Cao
```
1. Khởi động pmon
2. Nhấn c
3. Nhập: 50
4. Nhấn Enter
→ Chỉ hiển thị tiến trình dùng ≥ 50% CPU
```

### Ví Dụ 3: Tìm Tiến Trình Python Đang Chạy
```
1. Khởi động pmon
2. Nhấn /
3. Nhập: python
4. Nhấn Enter
→ Hiển thị tất cả tiến trình Python
```

### Ví Dụ 4: Tạm Dừng Tiến Trình Để Giải Phóng CPU
```
1. Chọn tiến trình bằng ↑/↓
2. Nhấn s (SIGSTOP)
3. Nhấn y để xác nhận
→ Tiến trình tạm dừng, CPU được giải phóng
4. Để tiếp tục: chọn lại tiến trình, nhấn C (SIGCONT)
```

### Ví Dụ 5: Kết Hợp Nhiều Bộ Lọc
```
1. Nhấn /, nhập: python, Enter
2. Nhấn c, nhập: 10, Enter
3. Nhấn m, nhập: 5, Enter
→ Hiển thị tiến trình Python với CPU ≥ 10% và Memory ≥ 5%
```

## Xử Lý Lỗi

### Lỗi "curses error"
**Nguyên nhân:**
- Terminal không hỗ trợ curses
- Biến môi trường TERM không đúng
- Terminal quá nhỏ

**Giải pháp:**
```bash
export TERM=xterm-256color
```

### Lỗi "Permission denied" khi gửi tín hiệu
**Nguyên nhân:**
- Không có quyền với tiến trình của user khác
- Tiến trình hệ thống được bảo vệ

**Giải pháp:**
- Chỉ kill tiến trình của user hiện tại
- Hoặc dùng sudo để chạy MiniShell

### Terminal quá nhỏ
**Giải pháp:**
- Resize terminal hoặc zoom out
- Kích thước tối thiểu: 80 cột x 24 dòng

## Lưu Ý Quan Trọng

⚠️ **Cảnh báo:**
- SIGKILL có thể làm mất dữ liệu chưa lưu
- Nên thử SIGTERM trước khi dùng SIGKILL
- Không kill các tiến trình hệ thống quan trọng
- Một số tiến trình không thể kill (init, systemd, etc.)

💡 **Tips:**
- Refresh interval thấp = cập nhật nhanh nhưng tốn CPU
- Dùng bộ lọc để giảm số tiến trình hiển thị
- Bộ lọc không phân biệt chữ hoa/thường
- Có thể reset bộ lọc bất cứ lúc nào với phím `r`

## Yêu Cầu Hệ Thống

- **Python**: 3.6 trở lên
- **Library**: psutil
- **Terminal**: Hỗ trợ curses (xterm, gnome-terminal, konsole, iTerm2, etc.)
- **Kích thước**: Tối thiểu 80x24 characters
- **OS**: Linux, macOS, hoặc Unix-like systems

## Cài Đặt Dependencies

```bash
pip install psutil
```

## Kết Luận

Process Monitor đã được nâng cấp toàn diện với các tính năng chính:

1. ✅ **Thông tin chi tiết**: Threads, I/O, STATUS, RUNTIME, màu sắc
2. ✅ **Quản lý danh sách lớn**: Phân trang, tìm kiếm
3. ✅ **Tương tác cao**: Gửi tín hiệu (KILL, TERM, STOP, CONT)
4. ✅ **Xử lý lỗi tốt**: Thông báo chi tiết, hướng dẫn khắc phục
5. ✅ **Tùy biến refresh**: Điều chỉnh real-time (0.5-10s)
6. ✅ **Lọc linh hoạt**: Tên, CPU, Memory (kết hợp được)

### Cập Nhật Mới Nhất:
- **STATUS column**: Hiển thị trạng thái hiện tại của tiến trình (Running, Sleeping, Stopped, etc.)
- **RUNTIME column**: Hiển thị tổng thời gian chạy của tiến trình với định dạng dễ đọc

Giờ đây bạn có thể giám sát và quản lý tiến trình hiệu quả hơn bao giờ hết!
