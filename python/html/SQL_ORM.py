import hashlib
import secrets
import sqlite3

PEPPER = "YourSuperSecretStaticPepper123!"


class Apartment(object):
    """מייצגת ישות של דירה / דייר בטבלת Users"""
    def __init__(self, owner, aprt_pass, street, flr, num, email, phone, accountID, isAdmin=False):
        self.owner = owner
        self.aprt_pass = aprt_pass
        self.street = street
        self.floor = flr
        self.num = num
        self.email = email
        self.phone = phone
        self.account_ID = accountID
        self.isAdmin = isAdmin

    def __str__(self):
        return f"Apartment: {self.owner} | Building: {self.account_ID} | Floor: {self.floor} | Apt: {self.num}"


class Building(object):
    """מייצגת ישות של בניין בטבלת Buildings"""
    def __init__(self, building_id, address, city, num_floors, has_elevator):
        self.building_id = building_id
        self.address = address
        self.city = city
        self.num_floors = num_floors
        self.has_elevator = has_elevator

    def __str__(self):
        return f"Building {self.building_id}: {self.address}, {self.city} | Floors: {self.num_floors} | Elevator: {self.has_elevator}"


class BuildingApartmentORM:
    """מחלקת ה-ORM הראשית המנהלת את מסד הנתונים של הבניינים והדירות"""
    def __init__(self):
        self.conn = None
        self.current = None
        self.init_db()

    def open_db(self):
        self.conn = sqlite3.connect('UserAccount.db')
        self.current = self.conn.cursor()

    def close_db(self):
        if self.conn:
            self.conn.close()

    def commit(self):
        if self.conn:
            self.conn.commit()

    def init_db(self):
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
            CREATE TABLE IF NOT EXISTS Buildings (
                BuildingID INTEGER PRIMARY KEY AUTOINCREMENT,
                Address TEXT,
                City TEXT,
                NumFloors INTEGER,
                HasElevator TEXT
            )
        """)
        # Insert default building ID 1 so new users have a valid foreign key target
        self.current.execute("""
            INSERT OR IGNORE INTO Buildings (BuildingID, Address, City, NumFloors, HasElevator)
            VALUES (1, 'Main St 1', 'Default City', 4, 'True')
        """)
        self.commit()
        self.close_db()

    # --- שירותי בניינים ---
    def insert_building(self, building):
        self.open_db()
        try:
            sql = "INSERT INTO Buildings (Address, City, NumFloors, HasElevator) VALUES (?, ?, ?, ?)"
            self.current.execute(sql, (building.address, building.city, building.num_floors, str(building.has_elevator)))
            self.commit()
            self.close_db()
            return True
        except Exception as e:
            print("Error inserting building:", e)
            self.close_db()
            return False

    def get_all_buildings(self):
        self.open_db()
        try:
            res = self.current.execute("SELECT * FROM Buildings").fetchall()
            self.close_db()
            return res
        except Exception as e:
            print("Error fetching buildings:", e)
            self.close_db()
            return None

    def sum_rent_by_building(self, building_id):
        """שאילתת אגרגציה לבניין"""
        self.open_db()
        try:
            sql = "SELECT SUM(CAST(Floor AS INTEGER)) FROM Users WHERE Accountid = ?"
            res = self.current.execute(sql, (building_id,)).fetchone()
            self.close_db()
            return res[0] if res and res[0] is not None else 0
        except Exception as e:
            print("Error calculating rent:", e)
            self.close_db()
            return 0

    # --- שירותי דירות ומשתמשים ---
    def get_apts_by_building_vulnerable(self, building_id):
        """שירות פגיע ל-SQL Injection לצורך הדגמה"""
        self.open_db()
        try:
            sql = "SELECT * FROM Users WHERE Accountid = " + str(building_id)
            res = self.current.execute(sql).fetchall()
            self.close_db()
            return res
        except Exception as e:
            print("Error fetching apts (vulnerable):", e)
            self.close_db()
            return None

    def get_user_credentials(self, username):
        self.open_db()
        sql = "SELECT salt, password_hash FROM Users WHERE Username = ?"
        res = self.current.execute(sql, (username,)).fetchone()
        self.close_db()
        if res:
            return {'salt': res[0], 'password_hash': res[1]}
        return None

    def insert_new_account(self, user, building_id=1):
        self.open_db()
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
                building_id, str(user.isAdmin)
            ))
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
            self.current.execute(sql, (owner,))
            self.commit()
            self.close_db()
            return True
        except Exception as e:
            print("DB Delete Error:", e)
            self.close_db()
            return False

    def get_users(self):
        self.open_db()
        try:
            res = self.current.execute("SELECT * FROM Users").fetchall()
            self.close_db()
            return res
        except Exception as e:
            self.close_db()
            return None

    def update_user(self, user):
        self.open_db()
        try:
            sql = "UPDATE Users SET Street = ?, Floor = ?, Num = ?, Email = ?, Phone = ? WHERE Username = ?"
            self.current.execute(sql, (
                user.street, user.floor, user.num, user.email, user.phone, user.owner
            ))
            self.commit()
            self.close_db()
            return True
        except Exception as e:
            print("DB Update Error:", e)
            self.close_db()
            return False