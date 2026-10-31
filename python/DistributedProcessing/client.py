__author__ = 'Yossi'

import hashlib
import multiprocessing
# 2.6  client server October 2021

import socket
import sys
import threading
import traceback
from dataclasses import fields

from utils import send_with_size, recv_by_size
TASKS_TO_DO = []
TASKS_CURRENT = []
TASKS_DONE = []
CHUNK_SIZE = 0
STR_TO_FIND = ""
sock = None
found = False
found_num = -1
socket_lock = threading.Lock()

def handle_reply(data):
    global TASKS_TO_DO
    global CHUNK_SIZE
    global STR_TO_FIND

    action = data.split('~')[0]
    fields = data.split('~')[1:]
    match action:
        case "START":
            CHUNK_SIZE = int(fields[0])
            STR_TO_FIND = str(fields[1])
            for task in fields[2:-1]:
                TASKS_TO_DO.append(int(task))
        case "CONTI":
            CHUNK_SIZE = int(fields[0])
            STR_TO_FIND = str(fields[1])
            for task in fields[2:-1]:
                TASKS_TO_DO.append(int(task))


def find_str(task_num, chunk_size, str_to_find, child_conn, process_id, stop_flag):
    print(f"[Process-{process_id} - TASK {task_num}] Started.")
    ret_val = -1
    # if task_num == -1:
    #     child_conn.send("CLOSE~".encode())
    #     child_conn.close()
    #     return

    start = task_num*chunk_size
    end = start + chunk_size
    for i in range(start, end):
        if stop_flag.is_set():
            break
        # if i % (chunk_size//50) == 0:
        #     if child_conn.poll():
        #         data = child_conn.recv().decode()
        #         if data.split('~')[0] == "FOUND":
        #             break

        # md5_object = hashlib.md5(str(i).zfill(10).encode())
        md5_object = hashlib.md5(f"{i:010d}".encode())
        hex_hash = md5_object.hexdigest()
        if str(i) == "0012300456":
            print(f"Task {task_num}, {i} : {hex_hash}")
        if str(hex_hash).lower() == str(str_to_find).lower():
            ret_val = i
            break

    print(f"[Process-{process_id}] Finished.")

    child_conn.send(f"DONEC~{str(task_num)}~{str(ret_val)}".encode())
    child_conn.close()


def pipe_listener(parent_conn, process_id, stop_flag):
    global sock
    global TASKS_DONE
    global TASKS_CURRENT
    global found
    global found_num

    while not found:
        try:
            # This blocks ONLY this background thread, not the main application
            if parent_conn.poll(0.3):
                bdata = parent_conn.recv()

                data = bdata.decode()
                action = data.split('~')[0]
                task_num, ret_val = data.split('~')[1:]

                if action == "DONEC":
                    if int(ret_val) != -1:
                        found = True
                        found_num = (task_num, ret_val)
                        stop_flag.set()
                        with socket_lock:
                            send_with_size(sock, f"{action}~{task_num}~{ret_val}".encode())

                    else:
                        with socket_lock:
                            send_with_size(sock, f"{action}~{task_num}~{ret_val}".encode())

                    TASKS_DONE.append(int(task_num))
                    TASKS_CURRENT.remove(int(task_num))
                # elif action == "CLOSE":
                #     send_with_size(sock, "CLOSE~".encode())
                #     break

        except (EOFError, OSError):
            # Handles the case where the child process crashes or closes unexpectedly
            print(f"  [Thread-{process_id}] Pipe closed unexpectedly.")
            break


    # parent_conn.send("FOUND~".encode())
    parent_conn.close()


def main(ip, cpus_num, load_percent_num):
    """
    main client - handle socket and main loop
    """
    global TASKS_TO_DO
    global TASKS_CURRENT
    global TASKS_DONE
    global sock
    global CHUNK_SIZE
    global STR_TO_FIND

    connected = False
    sock = socket.socket()
    port = 33445
    sock.settimeout(0.1)

    try:
        sock.connect((ip, port))
        print(f'Connect succeeded {ip}:{port}')
        connected = True
    except:
        print(f'Error while trying to connect.  Check ip or port -- {ip}:{port}')

    processes = []
    threads = []
    i = 0

    stop_flag = multiprocessing.Event()

    with socket_lock:
        send_with_size(sock, f"READY~{cpus_num}~{load_percent_num}".encode())

    while connected:
        try:
            byte_data = recv_by_size(sock)
            if byte_data == b'':
                print('Seems server disconnected abnormal')
                break
            else:
                handle_reply(byte_data.decode())
        except TimeoutError:
            pass
        except socket.error as err:
            print(f'Got socket error: {err}')
            break
        except Exception as err:
            print(f'General error: {err}')
            print(traceback.format_exc())
            break

        while len(TASKS_TO_DO) > 0 and len(TASKS_CURRENT) < cpus_num and TASKS_TO_DO[0] != -1:
            parent_conn, child_conn = multiprocessing.Pipe()

            given_task = int(TASKS_TO_DO.pop(0))
            TASKS_CURRENT.append(given_task)

            p = multiprocessing.Process(target=find_str, args=(given_task, CHUNK_SIZE, STR_TO_FIND, child_conn, i, stop_flag))
            processes.append(p)

            t = threading.Thread(target=pipe_listener, args=(parent_conn, i, stop_flag))
            threads.append(t)

            p.start()
            t.start()
            i += 1

        if len(TASKS_TO_DO) > 0:

            if TASKS_TO_DO[0] == -1:
                print("All tasks completed or none available.")
                break

        elif len(TASKS_TO_DO) == 0 and len(TASKS_CURRENT) == 0:
            TASKS_DONE.clear()
            with socket_lock:
                send_with_size(sock, "MOREC~".encode())

    for p in processes:
        p.join()
    for t in threads:
        t.join()

    sock.close()
    print ('Bye')


if __name__ == '__main__':
    if len(sys.argv) >= 4:
        ip = sys.argv[1]
        cpus = int(sys.argv[2])
        load_percent = float(sys.argv[3])
        main(ip, cpus, load_percent)
    else:
        main('127.0.0.1', 1, 75)