import sys
import os
import time
import winreg
import win32gui
import win32process
import psutil

def add_to_registry():
    """רישום התוכנית ב-Registry של המשתמש הנוכחי"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        # נתיב ההרצה של הסקריפט / ה-EXE הנוכחי
        app_path = os.path.realpath(sys.argv[0])
        winreg.SetValueEx(key, "ProcessClub", 0, winreg.REG_SZ, f'"{app_path}"')
        winreg.CloseKey(key)
    except Exception:
        pass

def get_pids_with_windows():
    hwnds = []

    def enum_windows_callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            hwnds.append(hwnd)

    win32gui.EnumWindows(enum_windows_callback, None)

    pids = set()
    for hwnd in hwnds:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        pids.add(pid)
    return pids

def parse_list(list_path):
    if not os.path.exists(list_path):
        return []

    rules = []
    with open(list_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            exe_name = parts[0].lower()
            args = parts[1] if len(parts) > 1 else None
            rules.append((exe_name, args))
    return rules


def is_match(p_name, cmdline_list, rules):
    p_name_clean = p_name.lower()
    cmdline_args_str = " ".join(cmdline_list[1:]).lower() if len(cmdline_list) > 1 else ""

    for exe_name, args in rules:
        if p_name_clean == exe_name:
            if args is None:
                return True
            else:
                if args in cmdline_args_str:
                    return True
    return False


if __name__ == '__main__':
    os.makedirs("C:\\ProcessClub", exist_ok=True)
    add_to_registry()

    if len(sys.argv) < 2:
        mode = "build"
    else:
        mode = sys.argv[1]

    if mode == "build":
        window_pids = get_pids_with_windows()

        processes = list(psutil.process_iter(['pid', 'name', 'cmdline']))
        process_names = []

        for p in processes:
            if p.info['pid'] in window_pids:
                p_name = p.info['name'] or ""
                if p_name not in list(set(process_names)) and p_name.lower().endswith('.exe'):
                    cmdline = p.info['cmdline'] or []
                    if len(cmdline) > 1:
                        args_str = " ".join(cmdline[1:])
                        entry = f"{p_name} {args_str}"
                    else:
                        entry = p_name
                    process_names.append(entry)

        with open("C:\\ProcessClub\\WhiteClub.txt", "w") as f:
            for item in sorted(process_names):
                f.write(item + "\n")

    else:
        mode_path = "C:\\ProcessClub\\"
        mode_path += "WhiteClub.txt" if mode == "white" else "BlackClub.txt"
        process_names = parse_list(mode_path)

        while not os.path.isfile("C:\\ProcessClub\\stop.txt"):
            rules = parse_list(mode_path)
            window_pids = get_pids_with_windows()

            processes = list(psutil.process_iter(['pid', 'name', 'cmdline']))
            for p in processes:
                p_name = p.info['name'] or "Unknown"

                try:
                    if p.info['pid'] not in window_pids:
                        continue

                    p_name = p.info['name'] or ""
                    cmdline = p.info['cmdline'] or []

                    matched = is_match(p_name, cmdline, rules)

                    if mode == "white" and not matched:
                        p.kill()
                    elif mode == "black" and matched:
                        p.kill()

                except Exception as e:
                    print(f"Error: {e}")

            time.sleep(0.5)
