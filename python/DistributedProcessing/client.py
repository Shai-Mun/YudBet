__author__ = 'Yossi'
# 2.6  client server October 2021

import socket
import sys
import traceback

from utils import send_with_size, recv_by_size

def main(ip):
    """
    main client - handle socket and main loop
    """
    connected = False
    sock = socket.socket()
    port = 33445

    try:
        sock.connect((ip, port))
        print(f'Connect succeeded {ip}:{port}')
        connected = True
    except:
        print(f'Error while trying to connect.  Check ip or port -- {ip}:{port}')

    send_with_size(sock, "READY~".encode())
    while connected:
        try:
            byte_data = recv_by_size(sock)
            if byte_data == b'':
                print('Seems server disconnected abnormal')
                break
            else:
                print(byte_data.decode())

        except socket.error as err:
            print(f'Got socket error: {err}')
            break
        except Exception as err:
            print(f'General error: {err}')
            print(traceback.format_exc())
            break
    print ('Bye')
    sock.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main('127.0.0.1')