import random

from utils import send_with_size, recv_by_size
import socket
import sys
import threading

TASKS_NUM = 10000
TASKS_PER_CLIENT = 2
CHUNK_SIZE = 10000000000//TASKS_NUM
TASKS = []
TASKS_CURRENT = []
TASKS_DONE = []
found = False


class HandleClient(threading.Thread):
    def __init__(self, sock, tasks_per_client, str_to_find):
        super().__init__()
        self.sock = sock
        self.tasks_num = tasks_per_client
        self.str_to_find = str_to_find
        self.threads = [] # threading.Thread(target=None, args=(None, ))
        self.tasks = []

    def start(self):
        global TASKS
        global TASKS_CURRENT
        global TASKS_DONE
        global found

        while not found:
            try:
                data = recv_by_size(self.sock).decode()
                fields = data.split("~")
                if fields[0] == "READY":
                    cpus = int(fields[1])
                    load_percent = float(fields[2])
                    # Formula: CPUs * 2 tasks per CPU adjusted by load percentage
                    self.tasks_num = max(1, int(cpus * 2 * (load_percent / 100.0)))

                    to_send = "START~" + str(CHUNK_SIZE) + "~" + self.str_to_find + "~"
                    self.get_tasks()
                    for t in self.tasks:
                        to_send += str(t) + "~"

                    send_with_size(self.sock, to_send.encode())

                if fields[0] == "DONEC":
                    chunk = int(fields[1])
                    ret_val = fields[2]
                    if int(ret_val) != -1:
                        found = True
                        print(f"\n[SUCCESS] Password found! Number: {ret_val} (Chunk: {chunk})")
                    else:
                        if chunk in TASKS_DONE:
                            pass
                        else:
                            TASKS_DONE.append(chunk)
                        if chunk in TASKS_CURRENT:
                            TASKS_CURRENT.remove(chunk)

                if fields[0] == "MOREC":
                    to_send = "CONTI~" + str(CHUNK_SIZE) + "~" + self.str_to_find + "~"
                    self.get_tasks()
                    for t in self.tasks:
                        to_send += str(t) + "~"

                    send_with_size(self.sock, to_send.encode())


            except (TimeoutError, socket.timeout, ConnectionResetError, OSError):
                for n in self.tasks:
                    if n in TASKS_CURRENT:
                        TASKS_CURRENT.remove(n)
                    if n not in TASKS and n != -1:
                        TASKS.append(n)

                # if fields[0] == "CLOSE":
                #     self.sock.close()
                #     break
        print("bye")
        self.sock.close()


    def get_tasks(self):
        global TASKS
        global TASKS_CURRENT
        global TASKS_DONE
        self.tasks = []

        # test
        # n = 12
        # self.tasks.append(n)
        # TASKS.remove(n)
        # TASKS_CURRENT.append(n)

        if len(TASKS) > 0:
            for i in range(self.tasks_num):
                t = random.choice(TASKS)
                self.tasks.append(t)
                TASKS.remove(t)
                TASKS_CURRENT.append(t)
        else:
            self.tasks = [-1]


def main(str_to_find):
    global found
    global TASKS_PER_CLIENT
    global TASKS
    found = False

    s = socket.socket()
    s.bind(("0.0.0.0", 33445))
    s.listen(10)
    print("Server active on port 33445...")

    TASKS = [i for i in range(TASKS_NUM)]
    threads = []
    i = 1
    while not found:
        cli_s, addr = s.accept()
        cli_s.settimeout(10.0)
        t = HandleClient(cli_s, TASKS_PER_CLIENT, str_to_find)
        t.start()
        i += 1
        threads.append(t)

    for t in threads:
        t.sock.close()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Not enough parameters")

