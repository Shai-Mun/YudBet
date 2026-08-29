import socket
import threading
import hashlib
import time
from queue import Queue

import SQL_ORM
import enc_utils

exit_all = False
PEPPER = "YourSuperSecretStaticPepper123!"


def handl_client(sock, tid, db):
    global exit_all
    print(f"New Client num {tid}")

    try:
        method = enc_utils.recv_msg(sock).decode()
        if method == "DPH":
            encryption_key = enc_utils.dph_serv(sock)
        elif method == "RSA":
            encryption_key = enc_utils.rsa_serv(sock)
        else:
            sock.close()
            return

        is_authenticated = False

        while not exit_all:
            enc_data = enc_utils.recv_msg(sock)
            if not enc_data:
                break

            # Manual AES Decryption
            iv, ct = enc_data[:16], enc_data[16:]
            msg = enc_utils.aes_cbc_decrypt(ct, iv, encryption_key).decode()

            if not is_authenticated:
                if msg.startswith("LOGIN|"):
                    _, username, raw_password = msg.split('|', 2)
                    user_record = db.get_user_credentials(username)

                    if user_record:
                        salt, stored_hash = user_record['salt'], user_record['password_hash']
                        attempt_hash = hashlib.sha256((salt + raw_password + PEPPER).encode()).hexdigest()

                        if attempt_hash == stored_hash:
                            is_authenticated = True
                            ct_resp, iv_resp = enc_utils.aes_cbc_encrypt(b"LOGIN_OK", encryption_key)
                            enc_utils.send_msg(sock, iv_resp + ct_resp)
                            continue

                # Allow registration before login
                elif msg.startswith("INSUSR|"):
                    to_send = do_action(msg, db)
                    ct_resp, iv_resp = enc_utils.aes_cbc_encrypt(to_send.encode(), encryption_key)
                    enc_utils.send_msg(sock, iv_resp + ct_resp)
                    continue

                ct_resp, iv_resp = enc_utils.aes_cbc_encrypt(b"LOGIN_FAIL|Invalid credentials", encryption_key)
                enc_utils.send_msg(sock, iv_resp + ct_resp)
                continue

            to_send = do_action(msg, db)
            ct_resp, iv_resp = enc_utils.aes_cbc_encrypt(to_send.encode(), encryption_key)
            enc_utils.send_msg(sock, iv_resp + ct_resp)

    except Exception as err:
        print("Client Error:", err)
    finally:
        sock.close()


def do_action(data, db):
    """
    check what client ask and fill to send with the answer
    """
    to_send = "Not Set Yet"
    action = data[:6]
    data = data[7:]
    fields = data.split('|')
    try:
        if action == "UPDUSR":
            usr = SQL_ORM.Apartment(fields[0], fields[1], fields[2], fields[3], fields[4],
                                    fields[5], fields[6], 0, False)
            if db.update_user(usr):
                to_send = "UPDUSRR|" + "Success"
            else:
                to_send = "UPDUSRR|" + "Error"

        elif action == "INSUSR":
            user = SQL_ORM.Apartment(fields[0], fields[1], fields[2], fields[3], fields[4],
                                     fields[5], fields[6], 0, False)
            if db.insert_new_account(user):
                to_send = "INSUSRR|" + "Success"
            else:
                to_send = "INSUSRR|" + "Error"

        elif action == "DELUSR":
            user_record = db.get_user_credentials(fields[0])

            if user_record:
                salt, stored_hash = user_record['salt'], user_record['password_hash']
                attempt_hash = hashlib.sha256((salt + fields[1] + PEPPER).encode()).hexdigest()

                if attempt_hash == stored_hash:
                    print(db.del_user(fields[0]))
            to_send = "DELUSRR|" + "c"

        elif action == "GETUSR":
            to_send = "GETUSRR|" + "d"


        elif action == "RULIVE":
            to_send = "RULIVER|" + "yes i am a live server"

        else:
            print("Got unknown action from client " + action)
            to_send = "ERR___R|001|" + "unknown action"

    except Exception as e:
        print("Error:", e)
        to_send = "ERR___R|002|" + "error"

    return to_send


def q_manager(q, tid):
    global exit_all

    print("manager start:" + str(tid))
    while not exit_all:
        item = q.get()
        print("manager got somthing:" + str(item))
        # do some work with it(item)

        q.task_done()
        time.sleep(0.3)
    print("Manager say Bye")


def main():
    global exit_all

    exit_all = False
    db = SQL_ORM.UserAccountORM()

    s = socket.socket()

    q = Queue()

    q.put("Hi for start")

    manager = threading.Thread(target=q_manager, args=(q, 0))

    s.bind(("0.0.0.0", 33445))

    s.listen(4)
    print("after listen")

    threads = []
    i = 1
    while True:
        cli_s, addr = s.accept()
        t = threading.Thread(target=handl_client, args=(cli_s, i, db))
        t.start()
        i += 1
        threads.append(t)

    exit_all = True
    for t in threads:
        t.join()
    manager.join()

    s.close()


main()