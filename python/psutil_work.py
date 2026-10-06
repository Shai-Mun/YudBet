from concurrent.futures import ThreadPoolExecutor
import os
import psutil
import threading

open_files = {}
type_cnt = {}
pss = {}
per_exe = {}
dict_lock = threading.Lock()
psutil_lock = threading.Lock()

file_access_denied = 0
process_access_denied = 0

def process_worker(p):
    global file_access_denied, process_access_denied
    try:
        p_name = p.info['name'] or "Unknown"
        p_args = p.info['cmdline'] or []

        with dict_lock:
            pss[p.info['pid']] = (p_name, p_args)

    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        return
    except psutil.AccessDenied:
        with dict_lock:
            process_access_denied += 1
        return

    files = None
    try:
        with psutil_lock:
            files = p.open_files()
    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        return
    except psutil.AccessDenied:
        with dict_lock:
            file_access_denied += 1
        return

    if files:
        with dict_lock:
            for f in files:
                open_files.setdefault(f.path, []).append(p_name)

                _, ext = os.path.splitext(f.path)
                ext = ext.lstrip('.').lower() or 'NO_TYPE'
                type_cnt[ext] = type_cnt.get(ext, 0) + 1

                per_exe.setdefault(p_name, {})
                per_exe[p_name][ext] = per_exe[p_name].get(ext, 0) + 1


if __name__ == '__main__':
    processes = list(psutil.process_iter(['pid', 'name', 'cmdline']))

    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(process_worker, processes)

    print(f"\n\n\t\t PS len {len(pss)} \n\t\t ----------------")
    for pid, process in sorted(pss.items(), key=lambda item: item[1][0].lower()):
        print("\t\t", process[0], " $$$ ", pid, " $$$ ", " ".join(process[1]))

    print("\n2. All Files:")
    for path, process in sorted(open_files.items(), key=lambda x: x[0]):
        print(f"{path} ::: {process}")

    print("\n3. Types:")
    for ext, count in sorted(type_cnt.items(), key=lambda x: x[0]):
        print(f"\t\t{ext} - {count}")

    print("\n4. Exes Types:")
    for name, ext_counts in sorted(per_exe.items(), key=lambda x: x[0]):
        print(f"\n{name} ------ ")
        for ext, count in sorted(ext_counts.items(), key=lambda x: x[0]):
            print(f"\t\t{ext} - {count}")

    print(f"\n5. Processes Inspected: {len(pss)}")
    print(f"\t\tProcess Access Denied: {process_access_denied}")
    print(f"\t\tFile Access Denied: {file_access_denied}")

    print("\n6. Files Opened Twice Or More:")
    for path, process in sorted(open_files.items(), key=lambda x: x[0]):
        if len(list(set(process))) > 1:
            print(f"{path} ::: {list(set(process))}")

    user_input = input("\n7. Type a number/name of a process: ")
    try:
        if user_input.isnumeric():
            target_pid = int(user_input)
            for proc in processes:
                if proc.pid == target_pid:
                    proc.kill()
                    print(f"Process {target_pid} killed.")
        else:
            for proc in processes:
                if proc.info.get('name') == user_input:
                    proc.kill()
                    print(f"Process '{user_input}' (PID: {proc.pid}) killed.")

    except Exception as e:
        print(f"Error: {e}")