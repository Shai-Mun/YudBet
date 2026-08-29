import hashlib
import secrets
import sqlite3

import pickle
    # https://docs.python.org/2/library/sqlite3.html
    # https://www.youtube.com/watch?v=U7nfe4adDw8


__author__ = 'Yossi'

from math import floor

from pycparser.c_ast import Return

PEPPER = "YourSuperSecretStaticPepper123!"

class Apartment(object):
    def __init__(self,owner,aprt_pass,street,flr,num,email,phone,accountID,isAdmin):
        self.owner = owner
        self.aprt_pass = aprt_pass
        self.street = street
        self.floor = flr
        self.num = num
        self.email = email
        self.phone = phone
        self.account_ID = accountID
        self.isAdmin = isAdmin

    def new_pass(self,new_pass):
        self.aprt_pass= new_pass

    def change_manager_status(self):
        self.is_manager = not self.is_manager

    def __str__(self):
        return "apartment:"+self.owner+ ":"+self.aprt_pass+ ":"+self.street+ ":" + \
                      self.floor+":"+self.num+ ":"+self.phone+ ":"+self.email+ ":"+ \
                      str(self.account_ID)+":"+self.isAdmin

class Landlord(object):
    def __init__(self,acc_id,balance,manager,):
        self.id=acc_id
        self.balance=balance
        self.manager=manager
        self.credit_cards=[]





    
class UserAccountORM:
    def __init__(self):
        self.conn = None  # will store the DB connection
        self.cursor = None   # will store the DB connection cursor

        self.init_db()

    def open_db(self):
        """
        will open DB file and put value in:
        self.conn (need DB file name)
        and self.cursor
        """
        self.conn = sqlite3.connect('UserAccount.db')
        self.current = self.conn.cursor()
        
        
    def close_db(self):
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def init_db(self):
        """Creates table matching Apartment fields directly (no Fname/Lname)."""
        self.open_db()
        self.current.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                Username TEXT PRIMARY KEY,
                Password TEXT,
                salt TEXT,
                password_hash TEXT,
                Street TEXT,
                Floor TEXT,
                Num TEXT,
                Email TEXT,
                Phone TEXT,
                Accountid INTEGER,
                Isadmin TEXT
            )
        """)
        self.current.execute("""
            CREATE TABLE IF NOT EXISTS Accounts (
                Accountid INTEGER PRIMARY KEY,
                Balance REAL,
                Manager TEXT
            )
        """)
        self.commit()
        self.close_db()

    def get_user_credentials(self, username):
        """Fetches salt and password_hash for authentication."""
        self.open_db()
        sql = "SELECT salt, password_hash FROM Users WHERE Username = ?"
        res = self.current.execute(sql, (username,)).fetchone()
        self.close_db()
        if res:
            return {'salt': res[0], 'password_hash': res[1]}
        return None

    def insert_new_account(self,user):
        self.open_db()
        sql= "SELECT MAX(Accountid) FROM Accounts"
        res = self.current.execute(sql).fetchone()
        account_id = (res[0] + 1) if (res and res[0] is not None) else 1

        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((salt + user.aprt_pass + PEPPER).encode()).hexdigest()
        try:
            sql_user = """
                            INSERT INTO Users (Username, Password, salt, password_hash, Street, Floor, Num, Email, Phone, Accountid, Isadmin)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
            self.current.execute(sql_user, (
                user.owner, user.aprt_pass, salt, password_hash,
                user.street, user.floor, user.num, user.email, user.phone,
                account_id, str(user.isAdmin)
            ))

            sql_acc = "INSERT INTO Accounts (Accountid, Balance, Manager) VALUES (?, 0, ?)"
            self.current.execute(sql_acc, (account_id, user.owner))
            self.commit()
            self.close_db()
            return True

        except Exception as e:
            print("DB Insertion Error:", e)
            self.close_db()
            return False

    def del_user(self, owner):
        self.open_db()
        try:
            sql = "DELETE FROM Users WHERE Username = ?"
            res = self.current.execute(sql, (owner,)).fetchone()
            print(res)
            self.close_db()
            return True

        except Exception as e:
            print("DB Insertion Error:", e)
            self.close_db()
            return False

    def get_user(self, username):
        self.open_db()

        usr=None
        sql= "SELECT ................ "
        res= self.current.execute(sql)

        self.close_db()
        return usr
    
    def get_accounts(self):
        pass

    def get_users(self):
        self.open_db()
        res = self.current.execute("SELECT * FROM Users").fetchall()
        self.close_db()
        return res

    # def get_user_balance(self,username):
    #     self.open_db()
    #
    #     sql="SELECT a.Balance FROM Accounts a , Users b WHERE a.Accountid=b.Accountid and b.Username='"+username+"'"
    #     res = self.current.execute(sql)
    #     for ans in res:
    #         balance =  ans[0]
    #     self.close_db()
    #     return balance


    #__________________________________________________________________________________________________________________
    #__________________________________________________________________________________________________________________
    #______end of read start write ____________________________________________________________________________________
    #__________________________________________________________________________________________________________________
    #__________________________________________________________________________________________________________________
    #__________________________________________________________________________________________________________________




    #All write SQL

    def withdraw_by_username(self,amount,username):
        """
        return true for success and false if failed
        """
        pass

    def deposit_by_username(self,amount,username):
         pass

    def insert_new_user(self,username,password,firstname,lastname,address,phone,email,acid):
         pass

    def update_user(self,user):
        self.open_db()
        """
        Do here
        """
        self.close_db()
        return True

    def update_account(self,account):
        pass

    def delete_user(self,username):
        pass

    def delete_account(self,accountID):
        pass


def main_test():
    user1= Apartment("Yos", "12345", "yossi", "zahav", "kefar saba", "123123123", "1111", 1, '11')

    db= UserAccountORM()
    db.delete_user(user1.owner)
    users= db.get_users()
    for u in users :
        print(u)

if __name__ == "__main__":
    main_test()


