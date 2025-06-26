# ✅ main.py
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.pickers import MDDatePicker
from kivy.metrics import dp
import sqlite3
import pandas as pd
import os
from android.storage import primary_external_storage_path

KV = '''
ScreenManager:
    MainScreen:
    AddStudentScreen:
    AddPaymentScreen:
    ViewStudentsScreen:
    ViewPaymentsScreen:
    ExportScreen:

<MainScreen>:
    name: 'main'
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Student Management"
            elevation: 10
        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: dp(20)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDRaisedButton:
                    text: "Add Student"
                    on_release: app.root.current = 'add_student'
                MDRaisedButton:
                    text: "Add Payment"
                    on_release: app.root.current = 'add_payment'
                MDRaisedButton:
                    text: "View Students"
                    on_release: app.root.current = 'view_students'
                MDRaisedButton:
                    text: "View Payments"
                    on_release: app.root.current = 'view_payments'
                MDRaisedButton:
                    text: "Export to Excel"
                    on_release: app.root.current = 'export'

<AddStudentScreen>:
    name: 'add_student'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Add Student"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: dp(20)
                spacing: dp(15)
                size_hint_y: None
                height: self.minimum_height
                MDTextField:
                    id: name
                    hint_text: "Name"
                MDTextField:
                    id: aadhaar
                    hint_text: "Aadhaar"
                MDTextField:
                    id: qualification
                    hint_text: "Qualification"
                MDTextField:
                    id: course
                    hint_text: "Course Name"
                MDTextField:
                    id: phone
                    hint_text: "Phone No"
                MDTextField:
                    id: fees
                    hint_text: "Full Fees"
                    input_filter: 'float'
                MDTextField:
                    id: date
                    hint_text: "Date of Joining"
                    readonly: True
                    on_focus: if self.focus: root.show_date_picker()
                MDRaisedButton:
                    text: "Submit"
                    on_release: root.submit()

<AddPaymentScreen>:
    name: 'add_payment'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Add Payment"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(20)
            spacing: dp(10)
            MDTextField:
                id: aadhaar_phone
                hint_text: "Aadhaar or Phone"
            MDTextField:
                id: amount
                hint_text: "Amount Paid"
                input_filter: 'float'
            MDTextField:
                id: date
                hint_text: "Payment Date"
                readonly: True
                on_focus: if self.focus: root.show_date_picker()
            MDRaisedButton:
                text: "Submit"
                on_release: root.submit_payment()

<ViewStudentsScreen>:
    name: 'view_students'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "All Students"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
        BoxLayout:
            id: box

<ViewPaymentsScreen>:
    name: 'view_payments'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "All Payments"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
        BoxLayout:
            orientation: 'vertical'
            BoxLayout:
                id: table_container
                size_hint_y: 0.8
            ScrollView:
                size_hint_y: 0.2
                MDBoxLayout:
                    id: summary_container
                    orientation: 'vertical'
                    padding: dp(10)
                    spacing: dp(5)

<ExportScreen>:
    name: 'export'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: "Export to Excel"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
        MDBoxLayout:
            orientation: 'vertical'
            padding: dp(20)
            spacing: dp(20)
            MDRaisedButton:
                text: "Export Data"
                on_release: root.do_export()
'''

class MainScreen(Screen): pass
class AddStudentScreen(Screen):
    def show_date_picker(self):
        MDDatePicker(on_save=self.set_date).open()

    def set_date(self, instance, value, date_range):
        self.ids.date.text = str(value)

    def submit(self):
        data = {k: self.ids[k].text for k in ["name", "aadhaar", "qualification", "course", "phone", "fees", "date"]}
        if not all(data.values()):
            self.show_dialog("Error", "All fields are required.")
            return
        result = add_student(data)
        self.show_dialog("Student Entry", result)
        for k in data: self.ids[k].text = ""

    def show_dialog(self, title, text):
        dialog = MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())])
        dialog.open()

    def go_back(self): self.manager.current = 'main'

class AddPaymentScreen(Screen):
    def show_date_picker(self):
        MDDatePicker(on_save=self.set_date).open()

    def set_date(self, instance, value, date_range):
        self.ids.date.text = str(value)

    def submit_payment(self):
        try:
            amount = float(self.ids.amount.text)
        except:
            self.show_dialog("Error", "Enter valid amount.")
            return
        result = add_payment(self.ids.aadhaar_phone.text, amount, self.ids.date.text)
        self.show_dialog("Payment Entry", result)
        self.ids.aadhaar_phone.text = self.ids.amount.text = self.ids.date.text = ""

    def show_dialog(self, title, text):
        dialog = MDDialog(title=title, text=text, buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())])
        dialog.open()

    def go_back(self): self.manager.current = 'main'

class ViewStudentsScreen(Screen):
    def on_enter(self):
        self.ids.box.clear_widgets()
        students = get_all_students()
        if not students:
            self.ids.box.add_widget(MDLabel(text="No students found", halign="center"))
            return
        table = MDDataTable(size_hint=(1, 1), column_data=[("ID", dp(30)), ("Name", dp(40)), ("Aadhaar", dp(60)), ("Phone", dp(60)), ("Fees", dp(40)), ("Remain", dp(40))], row_data=[(str(s[0]), s[1], s[2], s[5], str(s[6]), str(s[7])) for s in students])
        self.ids.box.add_widget(table)

    def go_back(self): self.manager.current = 'main'

class ViewPaymentsScreen(Screen):
    def on_enter(self):
        self.ids.table_container.clear_widgets()
        self.ids.summary_container.clear_widgets()
        payments = get_all_payments()
        if not payments:
            self.ids.table_container.add_widget(MDLabel(text="No payments found", halign="center"))
            return
        table = MDDataTable(size_hint=(1, 1), column_data=[("PID", dp(30)), ("Name", dp(40)), ("Amount", dp(40)), ("Date", dp(60))], row_data=[(str(p[0]), p[2], str(p[4]), p[5]) for p in payments])
        self.ids.table_container.add_widget(table)
        total = sum(float(p[4]) for p in payments)
        self.ids.summary_container.add_widget(MDLabel(text=f"Total Amount Paid: ₹{total}", halign="center"))

    def go_back(self): self.manager.current = 'main'

class ExportScreen(Screen):
    def do_export(self):
        msg = export_data()
        dialog = MDDialog(title="Export", text=msg, buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())])
        dialog.open()

    def go_back(self): self.manager.current = 'main'

def create_tables():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY, name TEXT, aadhaar TEXT, qualification TEXT,
        course_name TEXT, phone_no TEXT, full_fees REAL, remaining_balance REAL, date_of_joining TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY, student_id INTEGER, amount_paid REAL,
        payment_date TEXT, FOREIGN KEY(student_id) REFERENCES students(id))""")
    conn.commit()
    conn.close()

def add_student(data):
    try:
        conn = sqlite3.connect("students.db")
        cur = conn.cursor()
        cur.execute("""INSERT INTO students
            (name, aadhaar, qualification, course_name, phone_no, full_fees, remaining_balance, date_of_joining)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["name"], data["aadhaar"], data["qualification"], data["course"],
             data["phone"], float(data["fees"]), float(data["fees"]), data["date"]))
        conn.commit()
        return "Student added."
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

def add_payment(aadhaar_or_phone, amount, date):
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()
    cur.execute("SELECT id, remaining_balance FROM students WHERE aadhaar=? OR phone_no=?", (aadhaar_or_phone, aadhaar_or_phone))
    student = cur.fetchone()
    if not student:
        return "Student not found."
    sid, remain = student
    if amount > remain:
        return "Amount exceeds balance."
    cur.execute("UPDATE students SET remaining_balance=? WHERE id=?", (remain - amount, sid))
    cur.execute("INSERT INTO payments (student_id, amount_paid, payment_date) VALUES (?, ?, ?)", (sid, amount, date))
    conn.commit()
    conn.close()
    return "Payment recorded."

def get_all_students():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM students")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_payments():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()
    cur.execute("SELECT p.payment_id, p.student_id, s.name, s.aadhaar, p.amount_paid, p.payment_date FROM payments p JOIN students s ON p.student_id = s.id")
    rows = cur.fetchall()
    conn.close()
    return rows

def export_data():
    try:
        export_dir = os.path.join(primary_external_storage_path(), "StudentAppExports")
        os.makedirs(export_dir, exist_ok=True)
        conn = sqlite3.connect("students.db")
        df1 = pd.read_sql_query("SELECT * FROM students", conn)
        df2 = pd.read_sql_query("SELECT * FROM payments", conn)
        df1.to_excel(os.path.join(export_dir, "students.xlsx"), index=False)
        df2.to_excel(os.path.join(export_dir, "payments.xlsx"), index=False)
        conn.close()
        return f"Exported to {export_dir}"
    except Exception as e:
        return f"Export failed: {str(e)}"

class StudentApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        create_tables()
        return Builder.load_string(KV)

if __name__ == '__main__':
    StudentApp().run()
