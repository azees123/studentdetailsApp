# main.py
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from kivymd.uix.pickers import MDDatePicker
import sqlite3
import pandas as pd
import os

# Android storage support
try:
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

# Create DB tables
def create_tables():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        aadhaar TEXT UNIQUE,
        qualification TEXT,
        course_name TEXT,
        phone_no TEXT,
        full_fees REAL,
        remaining_balance REAL,
        date_of_joining TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount_paid REAL,
        payment_date TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id))''')
    conn.commit()
    conn.close()

# Add student
def add_student(data):
    try:
        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO students 
            (name, aadhaar, qualification, course_name, phone_no, full_fees, remaining_balance, date_of_joining) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                       (data["name"], data["aadhaar"], data["qualification"], data["course_name"], data["phone_no"],
                        float(data["fees"]), float(data["fees"]), data["date_of_joining"]))
        conn.commit()
        return "Student added successfully."
    except sqlite3.IntegrityError:
        return "Error: Aadhaar already exists."
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

# Add payment
def add_payment(aadhaar_or_phone, amount, date):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, remaining_balance FROM students WHERE aadhaar=? OR phone_no=?",
                   (aadhaar_or_phone, aadhaar_or_phone))
    student = cursor.fetchone()
    if not student:
        return "Student not found."
    student_id, balance = student
    if amount > balance:
        return "Payment exceeds balance."
    new_balance = balance - amount
    cursor.execute("UPDATE students SET remaining_balance=? WHERE id=?", (new_balance, student_id))
    cursor.execute("INSERT INTO payments (student_id, amount_paid, payment_date) VALUES (?, ?, ?)",
                   (student_id, amount, date))
    conn.commit()
    conn.close()
    return "Payment recorded."

# Fetch all students
def get_all_students():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Fetch all payments
def get_all_payments():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.payment_id, p.student_id, s.name, s.aadhaar, p.amount_paid, p.payment_date
        FROM payments p
        JOIN students s ON p.student_id = s.id
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# Export CSV files
def export_data():
    try:
        conn = sqlite3.connect("students.db")
        students_df = pd.read_sql_query("SELECT * FROM students", conn)
        payments_df = pd.read_sql_query("SELECT * FROM payments", conn)

        if ANDROID:
            export_path = os.path.join(primary_external_storage_path(), "StudentAppExports")
        else:
            export_path = os.path.join(os.getcwd(), "exports")

        os.makedirs(export_path, exist_ok=True)

        students_df.to_csv(os.path.join(export_path, "students.csv"), index=False)
        payments_df.to_csv(os.path.join(export_path, "payments.csv"), index=False)

        conn.close()
        return f"Exported to: {export_path}"
    except Exception as e:
        return f"Export failed: {str(e)}"

# Screen classes
class MainScreen(Screen):
    pass

class AddStudentScreen(Screen):
    def submit(self):
        data = {
            "name": self.ids.name.text,
            "aadhaar": self.ids.aadhaar.text,
            "qualification": self.ids.qualification.text,
            "course_name": self.ids.course.text,
            "phone_no": self.ids.phone.text,
            "fees": self.ids.fees.text,
            "date_of_joining": self.ids.date.text,
        }
        result = add_student(data)
        self.dialog("Add Student", result)

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_date_selected)
        date_dialog.open()

    def on_date_selected(self, instance, value, date_range):
        self.ids.date.text = str(value)

    def dialog(self, title, text):
        self.dialog_instance = MDDialog(
            title=title,
            text=text,
            buttons=[MDFlatButton(text="OK", on_release=self.dismiss_dialog)]
        )
        self.dialog_instance.open()

    def dismiss_dialog(self, instance):
        self.dialog_instance.dismiss()

    def go_back(self):
        self.manager.current = 'main'

class AddPaymentScreen(Screen):
    def submit_payment(self):
        id_val = self.ids.aadhaar_phone.text
        try:
            amount = float(self.ids.amount.text)
        except ValueError:
            self.dialog("Invalid Input", "Amount must be a number.")
            return
        date = self.ids.date.text
        result = add_payment(id_val, amount, date)
        self.dialog("Add Payment", result)

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_date_selected)
        date_dialog.open()

    def on_date_selected(self, instance, value, date_range):
        self.ids.date.text = str(value)

    def dialog(self, title, text):
        self.dialog_instance = MDDialog(
            title=title,
            text=text,
            buttons=[MDFlatButton(text="OK", on_release=self.dismiss_dialog)]
        )
        self.dialog_instance.open()

    def dismiss_dialog(self, instance):
        self.dialog_instance.dismiss()

    def go_back(self):
        self.manager.current = 'main'

class ViewStudentsScreen(Screen):
    def on_enter(self):
        self.ids.box.clear_widgets()
        students = get_all_students()
        if not students:
            self.ids.box.add_widget(MDLabel(text="No students found", halign="center"))
            return

        table = MDDataTable(
            size_hint=(1, 1),
            column_data=[
                ("ID", dp(30)),
                ("Name", dp(50)),
                ("Aadhaar", dp(80)),
                ("Qualification", dp(60)),
                ("Course", dp(60)),
                ("Phone", dp(80)),
                ("Fees", dp(50)),
                ("Remaining", dp(60)),
                ("Join Date", dp(80)),
            ],
            row_data=[
                (
                    str(s[0]), s[1], s[2], s[3], s[4], s[5],
                    f"{s[6]:.2f}", f"{s[7]:.2f}", s[8]
                )
                for s in students
            ],
            use_pagination=True
        )
        self.ids.box.add_widget(table)

    def go_back(self):
        self.manager.current = 'main'

class ViewPaymentsScreen(Screen):
    def on_enter(self):
        self.ids.table_container.clear_widgets()
        self.ids.summary_container.clear_widgets()

        payments = get_all_payments()
        if not payments:
            self.ids.table_container.add_widget(
                MDLabel(text="No payments found", halign="center")
            )
            return

        table = MDDataTable(
            size_hint=(1, 1),
            column_data=[
                ("PID", dp(30)),
                ("Student ID", dp(30)),
                ("Name", dp(50)),
                ("Aadhaar", dp(80)),
                ("Amount", dp(50)),
                ("Date", dp(80)),
            ],
            row_data=[
                (
                    str(p[0]), str(p[1]), p[2], p[3],
                    f"{p[4]:.2f}", p[5]
                )
                for p in payments
            ],
            use_pagination=True
        )
        self.ids.table_container.add_widget(table)

        totals = {}
        for p in payments:
            student_id = p[1]
            amount = p[4]
            totals[student_id] = totals.get(student_id, 0) + amount

        for sid, total in sorted(totals.items()):
            self.ids.summary_container.add_widget(
                MDLabel(
                    text=f"Total paid by Student ID {sid}: ₹{total:.2f}",
                    halign="left",
                    theme_text_color="Secondary"
                )
            )

    def go_back(self):
        self.manager.current = 'main'

class ExportScreen(Screen):
    def do_export(self):
        msg = export_data()
        MDDialog(
            title="Export Result",
            text=msg,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.close(x))]
        ).open()

    def close(self, obj):
        obj.parent.parent.dismiss()

    def go_back(self):
        self.manager.current = 'main'

# App entry
class StudentApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        create_tables()
        return Builder.load_file("main.kv")

if __name__ == '__main__':
    StudentApp().run()
