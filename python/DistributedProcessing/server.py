from enc_utils import send_with_size, recv_by_size
import socket
import sys
import threading

TASKS_NUM = 10
found = False


class HandleClient(threading.Thread):
    def __init__(self, sock, tasks_num, str_to_find):
        super().__init__()
        self.sock = sock
        self.tasks_num = tasks_num
        self.str_to_find = str_to_find

    def start(self):
        send_with_size(self.sock, b'START~')


def main(str_to_find):
    global found
    global TASKS_NUM
    found = False

    s = socket.socket()
    s.bind(("0.0.0.0", 33445))
    s.listen(10)
    print("Server active on port 33445...")

    threads = []
    i = 1
    while not found:
        cli_s, addr = s.accept()
        t = HandleClient(cli_s, TASKS_NUM, str_to_find)
        t.start()
        i += 1
        threads.append(t)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Not enough parameters")


#
