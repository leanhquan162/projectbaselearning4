
import curses
import psutil
import time
import sys
import signal
import os
from typing import List, Dict, Optional


class ProcessFilter:
    """Class để quản lý bộ lọc tiến trình"""
    def __init__(self):
        self.name_filter = ""
        self.cpu_threshold = 0.0
        self.mem_threshold = 0.0
    
    def matches(self, proc_info: Dict) -> bool:
        """Kiểm tra xem tiến trình có khớp với bộ lọc không"""
        if self.name_filter and self.name_filter.lower() not in proc_info['name'].lower():
            return False
        if proc_info['cpu_percent'] < self.cpu_threshold:
            return False
        if proc_info['memory_percent'] < self.mem_threshold:
            return False
        return True
    
    def is_active(self) -> bool:
        """Kiểm tra xem có bộ lọc nào đang hoạt động không"""
        return bool(self.name_filter or self.cpu_threshold > 0 or self.mem_threshold > 0)
    
    def get_description(self) -> str:
        """Trả về mô tả bộ lọc hiện tại"""
        filters = []
        if self.name_filter:
            filters.append(f"name:'{self.name_filter}'")
        if self.cpu_threshold > 0:
            filters.append(f"CPU>{self.cpu_threshold}%")
        if self.mem_threshold > 0:
            filters.append(f"MEM>{self.mem_threshold}%")
        return " | ".join(filters) if filters else "None"


def get_process_info(proc: psutil.Process) -> Optional[Dict]:
    """Lấy thông tin chi tiết của một tiến trình"""
    try:
        with proc.oneshot():
            info = {
                'pid': proc.pid,
                'username': proc.username(),
                'cpu_percent': proc.cpu_percent(interval=0),
                'memory_percent': proc.memory_percent(),
                'name': proc.name(),
                'num_threads': proc.num_threads(),
                'status': proc.status(),
            }
            # Lấy thông tin I/O nếu có thể
            try:
                io_counters = proc.io_counters()
                info['io_read_bytes'] = io_counters.read_bytes
                info['io_write_bytes'] = io_counters.write_bytes
            except (psutil.AccessDenied, AttributeError):
                info['io_read_bytes'] = 0
                info['io_write_bytes'] = 0
            return info
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def format_bytes(bytes_val: int) -> str:
    """Format bytes thành dạng dễ đọc"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f}TB"


def show_process_monitor(stdscr):
    """
    Hàm này được gọi bởi curses, 'stdscr' là đối tượng màn hình.
    Cải thiện với nhiều tính năng mới.
    """
    try:
        # Cấu hình curses
        stdscr.nodelay(True)
        stdscr.clear()
        curses.curs_set(0)
        
        # Khởi tạo màu sắc
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)      # Màu đỏ cho CPU/MEM cao
        curses.init_pair(2, curses.COLOR_YELLOW, -1)   # Màu vàng cho CPU/MEM trung bình
        curses.init_pair(3, curses.COLOR_GREEN, -1)    # Màu xanh cho bình thường
        curses.init_pair(4, curses.COLOR_CYAN, -1)     # Màu cyan cho highlight
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Màu cho tiến trình được chọn
        
        # Biến trạng thái
        refresh_interval = 1.5  # Mặc định 1.5 giây
        current_page = 0
        processes_per_page = 15
        selected_row = 0
        process_filter = ProcessFilter()
        search_mode = False
        search_buffer = ""
        filter_mode = None  # 'name', 'cpu', 'mem', None
        filter_buffer = ""
        last_processes = []
        
        while True:
            try:
                # Lấy kích thước màn hình
                max_y, max_x = stdscr.getmaxyx()
                
                # 1. Xử lý phím bấm
                key = stdscr.getch()
                
                if key == ord('q'):  # Thoát
                    break
                elif key == ord('h'):  # Hiển thị help
                    show_help(stdscr)
                    stdscr.nodelay(True)
                    continue
                elif key == ord('+') or key == ord('='):  # Tăng refresh interval
                    refresh_interval = min(10.0, refresh_interval + 0.5)
                elif key == ord('-') or key == ord('_'):  # Giảm refresh interval
                    refresh_interval = max(0.5, refresh_interval - 0.5)
                elif key == curses.KEY_UP and not search_mode and not filter_mode:  # Di chuyển lên
                    selected_row = max(0, selected_row - 1)
                    if selected_row < current_page * processes_per_page:
                        current_page = max(0, current_page - 1)
                elif key == curses.KEY_DOWN and not search_mode and not filter_mode:  # Di chuyển xuống
                    selected_row = min(len(last_processes) - 1, selected_row + 1)
                    if selected_row >= (current_page + 1) * processes_per_page:
                        current_page += 1
                elif key == curses.KEY_PPAGE:  # Page Up
                    current_page = max(0, current_page - 1)
                    selected_row = current_page * processes_per_page
                elif key == curses.KEY_NPAGE:  # Page Down
                    max_page = max(0, (len(last_processes) - 1) // processes_per_page)
                    current_page = min(max_page, current_page + 1)
                    selected_row = current_page * processes_per_page
                elif key == ord('/'):  # Bắt đầu tìm kiếm theo tên
                    filter_mode = 'name'
                    filter_buffer = process_filter.name_filter
                elif key == ord('c'):  # Bắt đầu lọc theo CPU
                    filter_mode = 'cpu'
                    filter_buffer = str(int(process_filter.cpu_threshold)) if process_filter.cpu_threshold > 0 else ""
                elif key == ord('m'):  # Bắt đầu lọc theo Memory
                    filter_mode = 'mem'
                    filter_buffer = str(int(process_filter.mem_threshold)) if process_filter.mem_threshold > 0 else ""
                elif key == ord('r'):  # Reset bộ lọc
                    process_filter = ProcessFilter()
                    current_page = 0
                    selected_row = 0
                elif filter_mode:  # Đang ở chế độ nhập bộ lọc
                    if key == 10 or key == curses.KEY_ENTER:  # Enter
                        if filter_mode == 'name':
                            process_filter.name_filter = filter_buffer
                        elif filter_mode == 'cpu':
                            try:
                                process_filter.cpu_threshold = float(filter_buffer) if filter_buffer else 0.0
                            except ValueError:
                                process_filter.cpu_threshold = 0.0
                        elif filter_mode == 'mem':
                            try:
                                process_filter.mem_threshold = float(filter_buffer) if filter_buffer else 0.0
                            except ValueError:
                                process_filter.mem_threshold = 0.0
                        filter_mode = None
                        filter_buffer = ""
                        current_page = 0
                        selected_row = 0
                    elif key == 27:  # ESC
                        filter_mode = None
                        filter_buffer = ""
                    elif key in (curses.KEY_BACKSPACE, 127, 8):  # Backspace
                        filter_buffer = filter_buffer[:-1]
                    elif 32 <= key <= 126:  # Ký tự có thể in được
                        filter_buffer += chr(key)
                elif key == ord('k'):  # SIGKILL
                    send_signal_to_selected(stdscr, last_processes, selected_row, signal.SIGKILL, "SIGKILL")
                elif key == ord('t'):  # SIGTERM
                    send_signal_to_selected(stdscr, last_processes, selected_row, signal.SIGTERM, "SIGTERM")
                elif key == ord('s'):  # SIGSTOP
                    send_signal_to_selected(stdscr, last_processes, selected_row, signal.SIGSTOP, "SIGSTOP")
                elif key == ord('C'):  # SIGCONT (Shift+C)
                    send_signal_to_selected(stdscr, last_processes, selected_row, signal.SIGCONT, "SIGCONT")
                
                # 2. Xóa màn hình
                stdscr.clear()
                
                # 3. Lấy thông tin hệ thống
                cpu_percent = psutil.cpu_percent(interval=0)
                mem = psutil.virtual_memory()
                mem_percent = mem.percent
                
                # 4. Vẽ header
                header_row = 0
                try:
                    stdscr.addstr(header_row, 0, "MiniShell Process Monitor", curses.A_BOLD)
                    stdscr.addstr(header_row, 30, f"Refresh: {refresh_interval:.1f}s (+/- to adjust)", curses.A_DIM)
                    stdscr.addstr(header_row, max_x - 20, "Press 'h' for help", curses.A_DIM)
                except curses.error:
                    pass
                
                header_row += 1
                cpu_color = get_color_for_percentage(cpu_percent)
                mem_color = get_color_for_percentage(mem_percent)
                try:
                    stdscr.addstr(header_row, 0, f"CPU: [{cpu_percent:5.1f}%] ", curses.color_pair(cpu_color))
                    stdscr.addstr(header_row, 18, '█' * min(30, int(cpu_percent * 30 / 100)), curses.color_pair(cpu_color))
                except curses.error:
                    pass
                
                header_row += 1
                try:
                    stdscr.addstr(header_row, 0, f"MEM: [{mem_percent:5.1f}%] ", curses.color_pair(mem_color))
                    stdscr.addstr(header_row, 18, '█' * min(30, int(mem_percent * 30 / 100)), curses.color_pair(mem_color))
                except curses.error:
                    pass
                
                # Hiển thị bộ lọc đang hoạt động
                header_row += 1
                if process_filter.is_active():
                    try:
                        stdscr.addstr(header_row, 0, f"Filter: {process_filter.get_description()}", curses.color_pair(4))
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addstr(header_row, 0, "Filter: None (/ for name, c for CPU, m for Memory, r to reset)", curses.A_DIM)
                    except curses.error:
                        pass
                
                # Hiển thị chế độ nhập bộ lọc
                if filter_mode:
                    header_row += 1
                    filter_prompts = {
                        'name': "Enter process name (substring): ",
                        'cpu': "Enter minimum CPU % (e.g., 10): ",
                        'mem': "Enter minimum Memory % (e.g., 20): "
                    }
                    try:
                        stdscr.addstr(header_row, 0, filter_prompts.get(filter_mode, ""), curses.color_pair(4) | curses.A_BOLD)
                        stdscr.addstr(header_row, len(filter_prompts.get(filter_mode, "")), filter_buffer)
                        stdscr.addstr(header_row, len(filter_prompts.get(filter_mode, "")) + len(filter_buffer), "_", curses.A_BLINK)
                    except curses.error:
                        pass
                
                # 5. Vẽ header bảng
                table_start_row = header_row + 2
                try:
                    stdscr.addstr(table_start_row, 0, 
                                 f"{'PID':<8}{'USER':<12}{'%CPU':>6} {'%MEM':>7}{'THR':>5}{'I/O R':>9}{'I/O W':>9} {'COMMAND':<20}",
                                 curses.A_BOLD | curses.A_UNDERLINE)
                except curses.error:
                    pass
                
                # 6. Lấy và lọc danh sách tiến trình
                procs = []
                for p in psutil.process_iter():
                    info = get_process_info(p)
                    if info and process_filter.matches(info):
                        procs.append(info)
                
                # Sắp xếp theo %CPU giảm dần
                procs_sorted = sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)
                last_processes = procs_sorted
                
                # Tính toán phân trang
                total_procs = len(procs_sorted)
                max_page = max(0, (total_procs - 1) // processes_per_page)
                current_page = min(current_page, max_page)
                start_idx = current_page * processes_per_page
                end_idx = min(start_idx + processes_per_page, total_procs)
                
                # Đảm bảo selected_row hợp lệ
                selected_row = min(selected_row, total_procs - 1) if total_procs > 0 else 0
                
                # 7. Vẽ danh sách tiến trình
                row = table_start_row + 1
                for idx in range(start_idx, end_idx):
                    if row >= max_y - 2:
                        break
                    
                    p = procs_sorted[idx]
                    user = p['username'] if p['username'] else 'N/A'
                    user_str = user[:10]
                    cmd_str = p['name'][:18]
                    
                    # Xác định màu dựa trên mức sử dụng tài nguyên
                    color = get_color_for_percentage(max(p['cpu_percent'], p['memory_percent']))
                    
                    # Highlight tiến trình được chọn
                    attr = curses.color_pair(color)
                    if idx == selected_row:
                        attr = curses.color_pair(5) | curses.A_BOLD
                    
                    line = f"{p['pid']:<8}{user_str:<12}{p['cpu_percent']:>6.1f} {p['memory_percent']:>7.1f}{p['num_threads']:>5}{format_bytes(p['io_read_bytes']):>9}{format_bytes(p['io_write_bytes']):>9} {cmd_str:<20}"
                    
                    try:
                        stdscr.addstr(row, 0, line[:max_x-1], attr)
                    except curses.error:
                        pass
                    row += 1
                
                # 8. Vẽ footer với thông tin phân trang và hướng dẫn
                footer_row = max_y - 2
                try:
                    page_info = f"Page {current_page + 1}/{max_page + 1} | Total: {total_procs} processes | Selected: {selected_row + 1}/{total_procs if total_procs > 0 else 0}"
                    stdscr.addstr(footer_row, 0, page_info, curses.A_DIM)
                except curses.error:
                    pass
                
                footer_row += 1
                try:
                    controls = "↑↓:Select | PgUp/PgDn:Page | k:Kill | t:Term | s:Stop | C:Cont | q:Quit"
                    stdscr.addstr(footer_row, 0, controls[:max_x-1], curses.A_DIM)
                except curses.error:
                    pass
                
                # 9. Cập nhật màn hình
                stdscr.refresh()
                
                # 10. Chờ theo refresh interval
                time.sleep(refresh_interval)
                
            except curses.error as e:
                # Xử lý lỗi curses cụ thể trong vòng lặp
                continue
            except KeyboardInterrupt:
                break
                
    except curses.error as e:
        # Xử lý lỗi curses toàn cục
        curses.endwin()
        print(f"\n❌ Lỗi Curses: {e}")
        print("\n📋 Hướng dẫn xử lý:")
        print("  1. Đảm bảo terminal của bạn hỗ trợ curses (không dùng terminal đơn giản)")
        print("  2. Thử chạy lại với terminal đầy đủ tính năng (xterm, gnome-terminal, etc.)")
        print("  3. Kiểm tra biến môi trường TERM: echo $TERM")
        print("  4. Thử: export TERM=xterm-256color")
        print("  5. Đảm bảo kích thước terminal đủ lớn (ít nhất 80x24)")
        sys.exit(1)
    except Exception as e:
        # Xử lý các lỗi khác
        curses.endwin()
        print(f"\n❌ Lỗi không mong đợi: {e}")
        print(f"   Loại lỗi: {type(e).__name__}")
        import traceback
        print("\n📋 Chi tiết lỗi:")
        traceback.print_exc()
        sys.exit(1)


def get_color_for_percentage(percentage: float) -> int:
    """Trả về mã màu dựa trên phần trăm sử dụng"""
    if percentage >= 80:
        return 1  # Đỏ
    elif percentage >= 50:
        return 2  # Vàng
    else:
        return 3  # Xanh


def send_signal_to_selected(stdscr, processes: List[Dict], selected_idx: int, sig: int, sig_name: str):
    """Gửi tín hiệu tới tiến trình được chọn"""
    if not processes or selected_idx >= len(processes):
        return
    
    proc_info = processes[selected_idx]
    pid = proc_info['pid']
    
    # Hiển thị hộp thoại xác nhận
    max_y, max_x = stdscr.getmaxyx()
    msg_lines = [
        "┌─────────────────────────────────────────┐",
        f"│ Send {sig_name} to process?            │",
        f"│ PID: {pid:<6} Name: {proc_info['name'][:15]:<15} │",
        "│                                         │",
        "│ Press 'y' to confirm, any key to cancel│",
        "└─────────────────────────────────────────┘"
    ]
    
    start_y = (max_y - len(msg_lines)) // 2
    start_x = (max_x - len(msg_lines[0])) // 2
    
    # Vẽ hộp thoại
    for i, line in enumerate(msg_lines):
        try:
            stdscr.addstr(start_y + i, start_x, line, curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass
    
    stdscr.refresh()
    
    # Đợi xác nhận
    stdscr.nodelay(False)
    key = stdscr.getch()
    stdscr.nodelay(True)
    
    if key == ord('y') or key == ord('Y'):
        try:
            os.kill(pid, sig)
            result_msg = f"✓ Sent {sig_name} to PID {pid}"
        except ProcessLookupError:
            result_msg = f"✗ Process {pid} not found"
        except PermissionError:
            result_msg = f"✗ Permission denied for PID {pid}"
        except Exception as e:
            result_msg = f"✗ Error: {e}"
        
        # Hiển thị kết quả
        try:
            stdscr.addstr(start_y + 3, start_x + 2, " " * (len(msg_lines[0]) - 4))
            stdscr.addstr(start_y + 3, start_x + 2, result_msg[:len(msg_lines[0]) - 4])
        except curses.error:
            pass
        stdscr.refresh()
        time.sleep(1.5)


def show_help(stdscr):
    """Hiển thị màn hình help"""
    stdscr.clear()
    curses.curs_set(0)
    
    help_text = [
        "═══════════════════════════════════════════════════════════════",
        "         MiniShell Process Monitor - Help                     ",
        "═══════════════════════════════════════════════════════════════",
        "",
        "NAVIGATION:",
        "  ↑/↓         - Move selection up/down",
        "  PgUp/PgDn   - Navigate pages",
        "",
        "SIGNALS:",
        "  k           - Send SIGKILL to selected process",
        "  t           - Send SIGTERM to selected process",
        "  s           - Send SIGSTOP to selected process",
        "  C (Shift+C) - Send SIGCONT to selected process",
        "",
        "FILTERING:",
        "  /           - Filter by process name",
        "  c           - Filter by minimum CPU usage (%)",
        "  m           - Filter by minimum Memory usage (%)",
        "  r           - Reset all filters",
        "",
        "DISPLAY:",
        "  +/=         - Increase refresh interval",
        "  -/_         - Decrease refresh interval",
        "",
        "OTHER:",
        "  h           - Show this help",
        "  q           - Quit",
        "",
        "COLOR CODING:",
        "  🟢 Green    - Normal usage (< 50%)",
        "  🟡 Yellow   - Medium usage (50-80%)",
        "  🔴 Red      - High usage (> 80%)",
        "",
        "═══════════════════════════════════════════════════════════════",
        "Press any key to return..."
    ]
    
    max_y, max_x = stdscr.getmaxyx()
    start_row = max(0, (max_y - len(help_text)) // 2)
    
    for i, line in enumerate(help_text):
        if start_row + i < max_y:
            try:
                stdscr.addstr(start_row + i, 2, line[:max_x-3])
            except curses.error:
                pass
    
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()


def start_tui():
    """Hàm bao bọc để khởi động và dọn dẹp curses an toàn."""
    try:
        curses.wrapper(show_process_monitor)
    except curses.error as e:
        print(f"\n❌ Lỗi Curses: Không thể khởi động giao diện.")
        print(f"   Chi tiết: {e}")
        print("\n📋 Nguyên nhân có thể:")
        print("  • Terminal không hỗ trợ curses")
        print("  • Kích thước terminal quá nhỏ")
        print("  • Biến môi trường TERM không được thiết lập đúng")
        print("\n💡 Giải pháp:")
        print("  1. Sử dụng terminal đầy đủ tính năng (xterm, gnome-terminal, konsole, etc.)")
        print("  2. Thử: export TERM=xterm-256color")
        print("  3. Đảm bảo terminal có kích thước tối thiểu 80x24")
        print("  4. Chạy lại từ terminal khác")
    except Exception as e:
        print(f"\n❌ Lỗi không mong đợi: {e}")
        import traceback
        traceback.print_exc()
