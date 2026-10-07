import sys
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

if __name__ == '__main__':
    if len(sys.argv) < 2:
        mode = "build"
    else:
        mode = sys.argv[1]

    if mode == "build":
        processes = list(psutil.process_iter(['name', 'cmdline']))
        process_names = []

        with open("C:\\ProcessClub\\WhiteClub.txt", "w") as f:
            for p in processes:
                p_name = p.info['name'] or "Unknown"
                if p_name not in list(set(process_names)) and ".exe" in p_name:
                    process_names.append(p_name)
                    f.write(p_name + "\n")

    mode_path = "C:\\ProcessClub\\"
    mode_path += "WhiteClub.txt" if mode == "white" else "BlackClub.txt"
    with open(mode_path, "r") as f:
        process_names = f.read().split("\n")
    print(process_names)


    while not os.path.isfile("C:\\ProcessClub\\stop.txt"):
        processes = list(psutil.process_iter(['name', 'cmdline']))
        for p in processes:
            p_name = p.info['name'] or "Unknown"

            try:
                if mode == "white":
                    if p_name not in process_names:
                        p.kill()
                elif mode == "black":
                    if p_name in process_names:
                        p.kill()
            except Exception as e:
                print(f"Error: {e}")
