import socket
import tkinter as tk
from tkinter import messagebox
import enc_utils


class SQLClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SQL Client GUI - Secured")
        self.root.geometry("480x550")

        self.encryption_key = ""
        self.cli_s = socket.socket()

        # Connect and exchange keys
        try:
            self.cli_s.connect(("127.0.0.1", 33445))
            self.encryption_key = enc_utils.dph_cli(self.cli_s)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server:\n{e}")
            self.root.after(10, self.root.destroy)
            return

        # Bind closing handler ONLY if connection succeeds
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.build_login_frame()
        self.build_main_frame()
        self.main_frame.pack_forget()

    def on_closing(self):
        try:
            self.cli_s.close()
        except Exception:
            pass
        self.root.destroy()

    def build_login_frame(self):
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(pady=20)

        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0, pady=5)
        self.login_user = tk.Entry(self.login_frame)
        self.login_user.grid(row=0, column=1, pady=5)

        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0, pady=5)
        self.login_pass = tk.Entry(self.login_frame, show="*")
        self.login_pass.grid(row=1, column=1, pady=5)

        tk.Button(self.login_frame, text="Login", command=self.attempt_login).grid(row=2, column=0, pady=10)
        tk.Button(self.login_frame, text="Register", command=self.open_register_window).grid(row=2, column=1, pady=10)

    def build_main_frame(self):
        self.main_frame = tk.Frame(self.root)

        # Top Action Buttons Navigation Frame
        nav_frame = tk.Frame(self.main_frame)
        nav_frame.grid(row=0, column=0, columnspan=2, pady=10)

        tk.Button(nav_frame, text="Insert User", command=lambda: self.show_action_form("INSUSR"), width=10).grid(row=0, column=0, padx=3)
        tk.Button(nav_frame, text="Update User", command=lambda: self.show_action_form("UPDUSR"), width=10).grid(row=0, column=1, padx=3)
        tk.Button(nav_frame, text="Delete User", command=lambda: self.show_action_form("DELUSR"), width=10).grid(row=0, column=2, padx=3)
        tk.Button(nav_frame, text="Get All Users", command=lambda: self.show_action_form("GETAUS"), width=10).grid(row=0, column=3, padx=3)

        # Dynamic Form Frame
        self.form_frame = tk.Frame(self.main_frame)
        self.form_frame.grid(row=1, column=0, columnspan=2, pady=10)

        # Server Response Console
        tk.Label(self.main_frame, text="Server Response:").grid(row=2, column=0, columnspan=2, sticky="w", padx=10)
        self.console = tk.Text(self.main_frame, height=10, width=54, state="disabled")
        self.console.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        # Initialize with Insert form by default
        self.show_action_form("INSUSR")

    def show_action_form(self, action):
        """Rebuilds the form area dynamically based on the selected action."""
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        self.current_entries = {}

        if action == "INSUSR":
            fields = ["Owner", "Apartment Password", "Street num", "Floor num", "Apartment num", "Email", "Phone"]
            btn_text = "Submit Insert"
            cmd = self.execute_insert
        elif action == "UPDUSR":
            fields = ["Owner", "Apartment Password", "Street num", "Floor num", "Apartment num", "Email", "Phone"]
            btn_text = "Submit Update"
            cmd = self.execute_update
        elif action == "DELUSR":
            fields = ["Owner", "Apartment Password"]
            btn_text = "Submit Delete"
            cmd = self.execute_delete
        elif action == "GETAUS":
            fields = []
            btn_text = "Fetch All Users"
            cmd = self.execute_get_users

        for idx, field in enumerate(fields):
            tk.Label(self.form_frame, text=field + ":").grid(row=idx, column=0, padx=5, pady=4, sticky="e")
            entry = tk.Entry(self.form_frame, width=28)
            if "Password" in field:
                entry.config(show="*")
            entry.grid(row=idx, column=1, padx=5, pady=4)
            self.current_entries[field] = entry

        row_idx = len(fields)
        tk.Button(self.form_frame, text=btn_text, command=cmd, width=16).grid(row=row_idx, column=0, columnspan=2, pady=10)

    def execute_insert(self):
        data = (
            f"INSUSR|{self.current_entries['Owner'].get()}|{self.current_entries['Apartment Password'].get()}|"
            f"{self.current_entries['Street num'].get()}|{self.current_entries['Floor num'].get()}|"
            f"{self.current_entries['Apartment num'].get()}|{self.current_entries['Email'].get()}|"
            f"{self.current_entries['Phone'].get()}"
        )
        self.send_and_receive(data)

    def execute_update(self):
        data = (
            f"UPDUSR|{self.current_entries['Owner'].get()}|{self.current_entries['Apartment Password'].get()}|"
            f"{self.current_entries['Street num'].get()}|{self.current_entries['Floor num'].get()}|"
            f"{self.current_entries['Apartment num'].get()}|{self.current_entries['Email'].get()}|"
            f"{self.current_entries['Phone'].get()}"
        )
        self.send_and_receive(data)

    def execute_delete(self):
        data = f"DELUSR|{self.current_entries['Owner'].get()}|{self.current_entries['Apartment Password'].get()}"
        self.send_and_receive(data)

    def execute_get_users(self):
        self.send_and_receive("GETAUS")

    def open_register_window(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Register New User")
        reg_win.geometry("350x350")

        reg_entries = {}
        fields = ["Owner", "Apartment Password", "Street num", "Floor num", "Apartment num", "Email", "Phone"]

        for idx, field in enumerate(fields):
            tk.Label(reg_win, text=field + ":").grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            entry = tk.Entry(reg_win, width=30)
            if "Password" in field:
                entry.config(show="*")
            entry.grid(row=idx, column=1, padx=10, pady=5)
            reg_entries[field] = entry

        def submit_registration():
            data = (
                f"INSUSR|{reg_entries['Owner'].get()}|{reg_entries['Apartment Password'].get()}|"
                f"{reg_entries['Street num'].get()}|{reg_entries['Floor num'].get()}|"
                f"{reg_entries['Apartment num'].get()}|{reg_entries['Email'].get()}|"
                f"{reg_entries['Phone'].get()}"
            )

            try:
                ct, iv = enc_utils.aes_cbc_encrypt(data.encode(), self.encryption_key)
                enc_utils.send_msg(self.cli_s, iv + ct)

                resp_enc = enc_utils.recv_msg(self.cli_s)
                if not resp_enc:
                    messagebox.showerror("Error", "Server disconnected.", parent=reg_win)
                    return

                iv_resp, ct_resp = resp_enc[:16], resp_enc[16:]
                response = enc_utils.aes_cbc_decrypt(ct_resp, iv_resp, self.encryption_key).decode()

                messagebox.showinfo("Server Response", response, parent=reg_win)
                if "OK" in response or "Success" in response:
                    reg_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Registration failed: {e}", parent=reg_win)

        tk.Button(reg_win, text="Submit", command=submit_registration).grid(row=len(fields), column=0, columnspan=2, pady=15)

    def attempt_login(self):
        user = self.login_user.get()
        pwd = self.login_pass.get()

        plaintext_msg = f"LOGIN|{user}|{pwd}"
        print(f"Client Sending (Plaintext): {plaintext_msg}")

        ct, iv = enc_utils.aes_cbc_encrypt(plaintext_msg.encode(), self.encryption_key)
        enc_utils.send_msg(self.cli_s, iv + ct)

        resp_enc = enc_utils.recv_msg(self.cli_s)
        iv_resp, ct_resp = resp_enc[:16], resp_enc[16:]
        resp = enc_utils.aes_cbc_decrypt(ct_resp, iv_resp, self.encryption_key).decode()

        print(f"Client Received (Plaintext): {resp}")

        if resp == "LOGIN_OK":
            self.login_frame.pack_forget()
            self.main_frame.pack(pady=10)
        else:
            messagebox.showerror("Error", "Invalid Login")

    def log_response(self, text):
        self.console.config(state="normal")
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)
        self.console.config(state="disabled")

    def send_and_receive(self, data):
        try:
            ct, iv = enc_utils.aes_cbc_encrypt(data.encode(), self.encryption_key)
            enc_utils.send_msg(self.cli_s, iv + ct)

            resp_enc = enc_utils.recv_msg(self.cli_s)
            if not resp_enc:
                self.log_response("Error: Server disconnected.")
                return

            iv_resp, ct_resp = resp_enc[:16], resp_enc[16:]
            response = enc_utils.aes_cbc_decrypt(ct_resp, iv_resp, self.encryption_key)
            self.log_response(f"Got>> {response.decode()}")
        except Exception as e:
            self.log_response(f"Socket Error: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SQLClientGUI(root)
    root.mainloop()