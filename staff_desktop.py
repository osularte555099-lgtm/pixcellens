import base64
import json
import os
import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from server import OfficeHandler
from http.server import ThreadingHTTPServer

API = (
    os.environ.get("PIXCELLENS_API")
    or os.environ.get("PIXCELLENS_PUBLIC_URL")
    or os.environ.get("PUBLIC_URL")
    or os.environ.get("APP_URL")
    or "https://pixcellens.onrender.com"
).rstrip("/")
PUBLIC_URL = (
    os.environ.get("PIXCELLENS_PUBLIC_URL")
    or os.environ.get("PUBLIC_URL")
    or os.environ.get("APP_URL")
    or "https://pixcellens.onrender.com"
).rstrip("/")


class StaffApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Picxellens Staff Portal")
        self.geometry("1180x720")
        self.minsize(980, 600)
        self.configure(bg="#eef2ef")
        self.records = []
        self.active_section = "Service Queue"
        self.setup_styles()
        self.build_layout()
        self.load_records()
        self.after(10000, self.refresh_loop)

    def setup_styles(self):
        styles = ttk.Style(self)
        styles.theme_use("clam")
        styles.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#26312d", rowheight=42, borderwidth=0, font=("Consolas", 10))
        styles.configure("Treeview.Heading", background="#edf0ee", foreground="#78817d", font=("Consolas", 9, "bold"), relief="flat", padding=10)
        styles.map("Treeview", background=[("selected", "#dce8df")], foreground=[("selected", "#26312d")])
        styles.configure("TNotebook", background="#ffffff", borderwidth=0)

    def build_layout(self):
        header = tk.Frame(self, bg="#fbfcfa", height=70, highlightbackground="#d5dbd7", highlightthickness=1)
        header.pack(fill="x")
        tk.Label(header, text="P", bg="#fbfcfa", fg="#26312d", font=("Georgia", 18), width=3, height=1, relief="groove").pack(side="left", padx=(24, 8), pady=16)
        tk.Label(header, text="PICXELLENS  /  STAFF APPLICATION", bg="#fbfcfa", fg="#26312d", font=("Georgia", 14, "bold")).pack(side="left")
        self.connection_label = tk.Label(header, text="Connecting...", bg="#fbfcfa", fg="#78817d", font=("Consolas", 10))
        self.connection_label.pack(side="right", padx=28)

        body = tk.Frame(self, bg="#fbfcfa")
        body.pack(fill="both", expand=True)
        sidebar = tk.Frame(body, bg="#f4f6f4", width=210, highlightbackground="#d5dbd7", highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        tk.Label(sidebar, text="STAFF WORKSPACE", bg="#f4f6f4", fg="#8a938e", font=("Consolas", 9), anchor="w").pack(fill="x", padx=24, pady=(28, 14))
        for name in ("Service Queue", "Students", "Customers", "Completed", "Reports", "Settings"):
            button = tk.Button(sidebar, text=name, command=lambda value=name: self.show_section(value), bg="#f4f6f4", fg="#78817d", activebackground="#e3e8e4", activeforeground="#26312d", relief="flat", anchor="w", padx=24, pady=12, font=("Consolas", 10), cursor="hand2")
            button.pack(fill="x")
            setattr(self, f"button_{name.replace(' ', '_').lower()}", button)
        tk.Label(sidebar, text="CUSTOMER CHECK-IN\n\nScan the QR code shown\nin the web staff portal.\n\nCustomers complete the\nform on their phone.", bg="#f4f6f4", fg="#8a938e", justify="left", anchor="nw", font=("Consolas", 9), padx=24).pack(fill="x", pady=(44, 0))

        self.content = tk.Frame(body, bg="#fbfcfa")
        self.content.pack(side="left", fill="both", expand=True, padx=42, pady=34)
        self.show_section("Service Queue")

    def clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def page_title(self, title, subtitle):
        tk.Label(self.content, text=title, bg="#fbfcfa", fg="#26312d", font=("Georgia", 25), anchor="w").pack(fill="x")
        tk.Label(self.content, text=subtitle, bg="#fbfcfa", fg="#78817d", font=("Consolas", 10), anchor="w").pack(fill="x", pady=(8, 26))

    def show_section(self, name):
        self.active_section = name
        self.clear_content()
        for section in ("Service Queue", "Students", "Customers", "Completed", "Reports", "Settings"):
            button = getattr(self, f"button_{section.replace(' ', '_').lower()}", None)
            if button:
                button.configure(bg="#e2e7e4" if section == name else "#f4f6f4", fg="#26312d" if section == name else "#78817d")
        if name == "Service Queue": self.queue_page()
        elif name == "Students": self.filtered_page("Students", "Student registrations grouped by school and queue status.", "Student")
        elif name == "Customers": self.filtered_page("Customers", "All customer registrations submitted from the QR form.", "Customer")
        elif name == "Completed": self.completed_page()
        elif name == "Reports": self.reports_page()
        else: self.settings_page()

    def stat_cards(self, values):
        row = tk.Frame(self.content, bg="#fbfcfa")
        row.pack(fill="x", pady=(0, 24))
        for label, value, color in values:
            card = tk.Frame(row, bg=color, highlightbackground="#cbd5cf", highlightthickness=1, width=180, height=78)
            card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            card.pack_propagate(False)
            tk.Label(card, text=str(value).zfill(2), bg=color, fg="#26312d", font=("Georgia", 22), anchor="w").pack(fill="x", padx=16, pady=(10, 0))
            tk.Label(card, text=label.upper(), bg=color, fg="#78817d", font=("Consolas", 8), anchor="w").pack(fill="x", padx=16)

    def table(self, columns, records, completed=False):
        frame = tk.Frame(self.content, bg="#ffffff", highlightbackground="#d5dbd7", highlightthickness=1)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for column in columns:
            tree.heading(column, text=column.upper())
            tree.column(column, width=130, anchor="w")
        for record in records:
            values = (record.get("queue", ""), record.get("name", ""), record.get("type", ""), record.get("service", ""), record.get("time", ""), record.get("status", ""))
            tree.insert("", "end", iid=str(record.get("id", record.get("queue", ""))), values=values)
        tree.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scroll.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scroll.set)
        if not completed:
            tk.Button(self.content, text="MARK SELECTED AS DONE", command=lambda: self.mark_selected(tree), bg="#26312d", fg="#ffffff", relief="flat", padx=16, pady=10, font=("Consolas", 9), cursor="hand2").pack(anchor="e", pady=14)

    def queue_page(self):
        self.page_title("Service Queue", "Customer registrations from the QR form appear here.")
        self.qr_card()
        waiting = len([r for r in self.records if r.get("status") == "Waiting"])
        done = len(self.records) - waiting
        self.stat_cards([("Total today", len(self.records), "#e0eaf0"), ("Waiting", waiting, "#f1eadb"), ("Completed", done, "#dce8df"), ("Services", 4, "#ffffff")])
        tk.Button(self.content, text="CALL NEXT QUEUE", command=self.call_next, bg="#47765b", fg="#ffffff", relief="flat", padx=18, pady=10, font=("Consolas", 9), cursor="hand2").pack(anchor="e", pady=(0, 14))
        self.table(("Queue", "Name", "Type", "Service", "Time in", "Status"), self.records)

    def qr_card(self):
        card = tk.Frame(self.content, bg="#f3f8f4", highlightbackground="#cbd8cf", highlightthickness=1, padx=18, pady=14)
        card.pack(fill="x", pady=(0, 24))
        text = tk.Frame(card, bg="#f3f8f4")
        text.pack(side="left", fill="both", expand=True)
        tk.Label(text, text="CUSTOMER CHECK-IN", bg="#f3f8f4", fg="#8a938e", font=("Consolas", 8), anchor="w").pack(fill="x", pady=(4, 8))
        tk.Label(text, text="Scan to join the queue", bg="#f3f8f4", fg="#26312d", font=("Georgia", 17), anchor="w").pack(fill="x")
        address = f"{PUBLIC_URL}/#register"
        tk.Label(text, text="Customers scan this code and complete the form on their phone.", bg="#f3f8f4", fg="#78817d", font=("Consolas", 9), anchor="w").pack(fill="x", pady=(6, 4))
        tk.Label(text, text=address, bg="#f3f8f4", fg="#47765b", font=("Consolas", 9), anchor="w").pack(fill="x")
        try:
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={quote(address)}"
            image_data = base64.b64encode(urlopen(qr_url, timeout=5).read()).decode("ascii")
            self.qr_photo = tk.PhotoImage(data=image_data)
            tk.Label(card, image=self.qr_photo, bg="#ffffff", padx=6, pady=6).pack(side="right")
        except Exception:
            tk.Label(card, text="QR\nunavailable", bg="#ffffff", fg="#78817d", width=14, height=6, font=("Consolas", 10)).pack(side="right")

    def filtered_page(self, title, subtitle, record_type):
        records = [record for record in self.records if record.get("type") == record_type]
        if record_type == "Student":
            school_names = sorted(set(record.get("school") or "Not provided" for record in records))
            filter_row = tk.Frame(self.content, bg="#fbfcfa")
            filter_row.pack(fill="x", pady=(0, 18))
            tk.Label(filter_row, text="GROUP STUDENTS BY SCHOOL", bg="#fbfcfa", fg="#78817d", font=("Consolas", 8)).pack(side="left", padx=(0, 12))
            school_var = tk.StringVar(value=getattr(self, "selected_school", "All Schools"))
            school_menu = ttk.Combobox(filter_row, textvariable=school_var, state="readonly", values=["All Schools", *school_names], width=30)
            school_menu.pack(side="left")
            school_menu.bind("<<ComboboxSelected>>", lambda event: self.filter_students(school_var.get()))
            if school_var.get() != "All Schools":
                records = [record for record in records if (record.get("school") or "Not provided") == school_var.get()]
        waiting = len([r for r in records if r.get("status") == "Waiting"])
        self.page_title(title, subtitle)
        self.stat_cards([("Total today", len(records), "#e0eaf0" if record_type == "Student" else "#f1eadb"), ("Pending", waiting, "#f1eadb"), ("Done", len(records) - waiting, "#dce8df"), ("Schools / services", len(set(r.get("school") or r.get("service") for r in records)), "#ffffff")])
        self.table(("Queue", "Name", "Type", "Service", "Time in", "Status"), records)

    def filter_students(self, school):
        self.selected_school = school
        self.show_section("Students")

    def completed_page(self):
        self.page_title("Completed", "Full history of finished photography sessions.")
        self.table(("Queue", "Name", "Type", "Service", "Time in", "Status"), [record for record in self.records if record.get("status") == "Done"], completed=True)

    def reports_page(self):
        self.page_title("Reports", "Quick operational summary for today.")
        services = {}
        for record in self.records: services[record.get("service", "Unknown")] = services.get(record.get("service", "Unknown"), 0) + 1
        top = max(services, key=services.get) if services else "No bookings yet"
        self.stat_cards([("Top service", top, "#e0eaf0"), ("Sessions completed", len([r for r in self.records if r.get("status") == "Done"]), "#dce8df"), ("Total registrations", len(self.records), "#ffffff")])

    def settings_page(self):
        self.page_title("Settings", "Manage studio information and customer check-in.")
        card = tk.Frame(self.content, bg="#ffffff", highlightbackground="#d5dbd7", highlightthickness=1, padx=24, pady=24)
        card.pack(fill="x", anchor="n")
        for label, value in (("Studio name", "Picxellens Photography Studio"), ("Contact number", ""), ("Address", "")):
            tk.Label(card, text=label.upper(), bg="#ffffff", fg="#78817d", font=("Consolas", 8), anchor="w").pack(fill="x", pady=(8, 5))
            entry = tk.Entry(card, relief="solid", bd=1, font=("Consolas", 10))
            entry.insert(0, value)
            entry.pack(fill="x", ipady=8)
        tk.Button(card, text="SAVE CHANGES", bg="#26312d", fg="#ffffff", relief="flat", padx=18, pady=10, font=("Consolas", 9), cursor="hand2").pack(anchor="e", pady=(20, 0))
        school_card = tk.Frame(self.content, bg="#ffffff", highlightbackground="#d5dbd7", highlightthickness=1, padx=24, pady=18)
        school_card.pack(fill="x", anchor="n", pady=(18, 0))
        tk.Label(school_card, text="SCHOOLS FOR STUDENT REGISTRATION", bg="#ffffff", fg="#78817d", font=("Consolas", 8), anchor="w").pack(fill="x", pady=(0, 8))
        school_row = tk.Frame(school_card, bg="#ffffff")
        school_row.pack(fill="x")
        self.school_entry = tk.Entry(school_row, relief="solid", bd=1, font=("Consolas", 10))
        self.school_entry.pack(side="left", fill="x", expand=True, ipady=8)
        tk.Button(school_row, text="ADD SCHOOL", command=self.add_school, bg="#26312d", fg="#ffffff", relief="flat", padx=14, pady=9, font=("Consolas", 9), cursor="hand2").pack(side="left", padx=(10, 0))
        try:
            schools = json.loads(api_request("/api/schools"))
        except Exception:
            schools = []
        tk.Label(school_card, text="  •  ".join(schools) or "No schools added", bg="#ffffff", fg="#47765b", font=("Consolas", 9), anchor="w", wraplength=700).pack(fill="x", pady=(14, 0))

    def add_school(self):
        school = self.school_entry.get().strip()
        if not school:
            messagebox.showwarning("Picxellens", "Enter a school name first.")
            return
        try:
            api_request("/api/schools", "POST", {"name": school})
            self.show_section("Settings")
            messagebox.showinfo("Picxellens", f"{school} is now available for student registration.")
        except Exception as error:
            messagebox.showerror("Connection error", str(error))

    def call_next(self):
        next_record = next((record for record in self.records if record.get("status") == "Waiting"), None)
        if not next_record:
            messagebox.showinfo("Picxellens", "There are no waiting registrations.")
            return
        try:
            api_request(f"/api/registrations/{next_record['id']}", "PATCH", {"status": "Called"})
            self.load_records()
            messagebox.showinfo("Call next queue", f"Please call queue {next_record['queue']} - {next_record['name']}.")
        except Exception as error:
            messagebox.showerror("Connection error", str(error))

    def mark_selected(self, tree):
        selection = tree.selection()
        if not selection: return
        try:
            api_request(f"/api/registrations/{selection[0]}", "PATCH", {"status": "Done"})
            self.load_records()
            messagebox.showinfo("Pixcellens", "Registration marked as completed.")
        except Exception as error:
            messagebox.showerror("Connection error", str(error))

    def load_records(self):
        try:
            self.records = json.loads(api_request("/api/registrations"))
            self.connection_label.configure(text="● Connected to office queue", fg="#47765b")
            self.show_section(self.active_section)
        except Exception:
            self.connection_label.configure(text="○ Start server.py to connect", fg="#a36e52")

    def refresh_loop(self):
        self.load_records()
        self.after(10000, self.refresh_loop)


def api_request(path, method="GET", payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(API + path, data=body, method=method, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=3) as response:
        return response.read().decode("utf-8")


def local_ip():
    connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        connection.connect(("8.8.8.8", 80))
        return connection.getsockname()[0]
    except OSError:
        return "localhost"
    finally:
        connection.close()


def start_local_server():
    global API
    if os.environ.get("PIXCELLENS_API"):
        return
    for port in range(8000, 8011):
        try:
            server = ThreadingHTTPServer(("0.0.0.0", port), OfficeHandler)
            API = f"http://localhost:{port}"
            threading.Thread(target=server.serve_forever, daemon=True).start()
            return
        except OSError:
            continue


if __name__ == "__main__":
    start_local_server()
    try:
        StaffApplication().mainloop()
    except URLError:
        messagebox.showerror("Pixcellens", "Start server.py before opening the staff application.")