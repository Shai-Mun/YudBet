import socket
import tkinter as tk
from tkinter import messagebox
import enc_utils


class SQLClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Building & Apartment Management GUI")
        self.root.geometry("560x640")

        self.encryption_key = ""
        self.cli_s = socket.socket()

        try:
            self.cli_s.connect(("127.0.0.1", 33445))
            self.encryption_key = enc_utils.dph_cli(self.cli_s)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server:\n{e}")
            self.root.after(10, self.root.destroy)
            return

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

        nav_frame = tk.Frame(self.main_frame)
        nav_frame.grid(row=0, column=0, columnspan=2, pady=10)

        # כפתורי פעולות בניינים ודירות בלבד (תואמי 10 השירותים)
        tk.Button(nav_frame, text="הוסף בניין", command=lambda: self.show_action_form("INSBLD"), width=12).grid(row=0, column=0, padx=2, pady=2)
        tk.Button(nav_frame, text="הצג בניינים", command=lambda: self.show_action_form("GETBLD"), width=12).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(nav_frame, text="חישוב הכנסה", command=lambda: self.show_action_form("SUMRNT"), width=12).grid(row=0, column=2, padx=2, pady=2)

        tk.Button(nav_frame, text="הוסף דירה", command=lambda: self.show_action_form("INSAPT"), width=12).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(nav_frame, text="חיפוש לפי בניין", command=lambda: self.show_action_form("GETABI"), width=12).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(nav_frame, text="עדכן דירה", command=lambda: self.show_action_form("UPDAPT"), width=12).grid(row=1, column=2, padx=2, pady=2)

        tk.Button(nav_frame, text="מחק דירה", command=lambda: self.show_action_form("DELAPT"), width=12).grid(row=2, column=0, padx=2, pady=2)
        tk.Button(nav_frame, text="הצג כל הדירות", command=lambda: self.show_action_form("GETAPT"), width=12).grid(row=2, column=1, padx=2, pady=2)

        self.form_frame = tk.Frame(self.main_frame)
        self.form_frame.grid(row=1, column=0, columnspan=2, pady=10)

        tk.Label(self.main_frame, text="Server Response:").grid(row=2, column=0, columnspan=2, sticky="w", padx=10)
        self.console = tk.Text(self.main_frame, height=12, width=64, state="disabled")
        self.console.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        self.show_action_form("INSBLD")

    def show_action_form(self, action):
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        self.current_entries = {}
        fields = []
        btn_text = ""
        cmd = None

        if action == "INSBLD":
            fields = ["Address", "City", "Num Floors", "Has Elevator"]
            btn_text = "Submit Building"
            cmd = self.execute_insert_building
        elif action == "GETBLD":
            btn_text = "Fetch All Buildings"
            cmd = lambda: self.send_and_receive("GETBLD")
        elif action == "SUMRNT":
            fields = ["Building ID"]
            btn_text = "Calculate Total Rent"
            cmd = self.execute_sum_rent
        elif action == "INSAPT":
            fields = ["Building ID", "Apartment Num", "Floor", "Resident Name"]
            btn_text = "Submit Apartment"
            cmd = self.execute_insert_apartment
        elif action == "GETABI":
            fields = ["Building ID"]
            btn_text = "Fetch Apartments in Building"
            cmd = self.execute_get_apts_by_bldg
        elif action == "UPDAPT":
            fields = ["Resident Name", "Phone", "Floor"]
            btn_text = "Submit Update"
            cmd = self.execute_update_apartment
        elif action == "DELAPT":
            fields = ["Resident Name"]
            btn_text = "Submit Delete"
            cmd = self.execute_delete_apartment
        elif action == "GETAPT":
            btn_text = "Fetch All Apartments"
            cmd = lambda: self.send_and_receive("GETAPT")

        for idx, field in enumerate(fields):
            tk.Label(self.form_frame, text=field + ":").grid(row=idx, column=0, padx=5, pady=3, sticky="e")
            entry = tk.Entry(self.form_frame, width=30)
            entry.grid(row=idx, column=1, padx=5, pady=3)
            self.current_entries[field] = entry

        row_idx = len(fields)
        tk.Button(self.form_frame, text=btn_text, command=cmd, width=22).grid(row=row_idx, column=0, columnspan=2, pady=8)

    def execute_insert_building(self):
        data = f"INSBLD|{self.current_entries['Address'].get()}|{self.current_entries['City'].get()}|{self.current_entries['Num Floors'].get()}|{self.current_entries['Has Elevator'].get()}"
        self.send_and_receive(data)

    def execute_sum_rent(self):
        data = f"SUMRNT|{self.current_entries['Building ID'].get()}"
        self.send_and_receive(data)

    def execute_insert_apartment(self):
        data = f"INSAPT|{self.current_entries['Building ID'].get()}|{self.current_entries['Apartment Num'].get()}|{self.current_entries['Floor'].get()}|{self.current_entries['Resident Name'].get()}"
        self.send_and_receive(data)

    def execute_get_apts_by_bldg(self):
        data = f"GETABI|{self.current_entries['Building ID'].get()}"
        self.send_and_receive(data)

    def execute_update_apartment(self):
        data = f"UPDAPT|{self.current_entries['Resident Name'].get()}|{self.current_entries['Phone'].get()}|{self.current_entries['Floor'].get()}"
        self.send_and_receive(data)

    def execute_delete_apartment(self):
        data = f"DELAPT|{self.current_entries['Resident Name'].get()}"
        self.send_and_receive(data)

    def open_register_window(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Register New User")
        reg_win.geometry("360x360")

        reg_entries = {}
        fields = ["Owner", "Apartment Password", "Street num", "Floor num", "Apartment num", "Email", "Phone"]

        for idx, field in enumerate(fields):
            tk.Label(reg_win, text=field + ":").grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            entry = tk.Entry(reg_win, width=28)
            if "Password" in field:
                entry.config(show="*")
            entry.grid(row=idx, column=1, padx=10, pady=5)
            reg_entries[field] = entry

        def submit_registration():
            # Sanitize inputs: strip whitespace and remove '|' to prevent server protocol errors
            owner = reg_entries['Owner'].get().strip().replace("|", "")
            pwd = reg_entries['Apartment Password'].get().replace("|", "")
            street = reg_entries['Street num'].get().strip().replace("|", "")
            floor = reg_entries['Floor num'].get().strip().replace("|", "")
            apt = reg_entries['Apartment num'].get().strip().replace("|", "")
            email = reg_entries['Email'].get().strip().replace("|", "")
            phone = reg_entries['Phone'].get().strip().replace("|", "")

            # Validation check for required fields
            if not owner or not pwd:
                messagebox.showwarning("Input Error", "Username and Password cannot be empty!", parent=reg_win)
                return

            data = f"INSUSR|{owner}|{pwd}|{street}|{floor}|{apt}|{email}|{phone}"

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
        ct, iv = enc_utils.aes_cbc_encrypt(plaintext_msg.encode(), self.encryption_key)
        enc_utils.send_msg(self.cli_s, iv + ct)

        resp_enc = enc_utils.recv_msg(self.cli_s)
        iv_resp, ct_resp = resp_enc[:16], resp_enc[16:]
        resp = enc_utils.aes_cbc_decrypt(ct_resp, iv_resp, self.encryption_key).decode()

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