__author__ = 'Yossi'

import hashlib
# 2.6  client server October 2021

import socket
import sys
import threading
import traceback

from utils import send_with_size, recv_by_size
TASKS_TO_DO = []
TASKS_DOING = []
CHUNK_SIZE = 0
STR_TO_FIND = ""

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
            for task in fields[2:]:
                TASKS_TO_DO.append(task)


def find_str(task_num):
    global STR_TO_FIND
    for i in range(task_num*CHUNK_SIZE, task_num*CHUNK_SIZE+CHUNK_SIZE):
        print(i)
        md5_object = hashlib.md5(str(i).zfill(10).encode('utf-8'))
        hex_hash = md5_object.hexdigest()
        if hex_hash == STR_TO_FIND:
            return True
    return False


def main(ip):
    """
    main client - handle socket and main loop
    """
    global TASKS_TO_DO
    global TASKS_DOING

    connected = False
    sock = socket.socket()
    port = 33445
    sock.settimeout(0.0)

    try:
        sock.connect((ip, port))
        print(f'Connect succeeded {ip}:{port}')
        connected = True
    except:
        print(f'Error while trying to connect.  Check ip or port -- {ip}:{port}')

    threads = []
    send_with_size(sock, "READY~".encode())
    while connected:
        try:
            byte_data = recv_by_size(sock)
            if byte_data == b'':
                print('Seems server disconnected abnormal')
                break
            else:
                pass
                # print(byte_data.decode())
        except TimeoutError:
            continue
        except socket.error as err:
            print(f'Got socket error: {err}')
            break
        except Exception as err:
            print(f'General error: {err}')
            print(traceback.format_exc())
            break

        if len(TASKS_TO_DO) > 0:
            t = threading.Thread(target=find_str, args=(TASKS_TO_DO[0]))
            TASKS_DOING.append(TASKS_TO_DO.pop(0))
            t.start()
            threads.append(t)


    print ('Bye')
    sock.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main('127.0.0.1')