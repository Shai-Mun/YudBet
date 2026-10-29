import random

from utils import send_with_size, recv_by_size
import socket
import sys
import threading

TASKS_NUM = 100
TASKS_PER_CLIENT = 10
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

        data = recv_by_size(self.sock).decode()
        fields = data.split("~")
        if fields[0] == "READY":
            to_send = "START~" + str(CHUNK_SIZE) + "~" + self.str_to_find + "~"
            self.get_tasks()
            for t in self.tasks:
                to_send += str(t) + "~"

            send_with_size(self.sock, to_send.encode())

    def get_tasks(self):
        global TASKS
        global TASKS_CURRENT
        global TASKS_DONE

        for i in range(TASKS_PER_CLIENT):
            t = random.choice(TASKS)
            self.tasks.append(t)
            TASKS.remove(t)
            TASKS_CURRENT.append(t)


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
        t = HandleClient(cli_s, TASKS_PER_CLIENT, str_to_find)
        t.start()
        i += 1
        threads.append(t)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Not enough parameters")


#
