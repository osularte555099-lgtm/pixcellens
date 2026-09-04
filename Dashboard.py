import io
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import qrcode
import streamlit as st


APP_NAME = "picxellens"
DB_PATH = Path(__file__).with_name("picxellens_queue.db")


def db_connection():
	connection = sqlite3.connect(DB_PATH)
	connection.row_factory = sqlite3.Row
	return connection


def initialize_database():
	with db_connection() as connection:
		connection.execute(
			"""
			CREATE TABLE IF NOT EXISTS queue_entries (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				ticket TEXT NOT NULL UNIQUE,
				customer_type TEXT NOT NULL,
				full_name TEXT NOT NULL,
				email TEXT NOT NULL,
				phone TEXT NOT NULL,
				section TEXT,
				student_id TEXT,
				grade_level TEXT,
				status TEXT NOT NULL DEFAULT 'Waiting',
				created_at TEXT NOT NULL
			)
			"""
		)


def add_queue_entry(customer_type, form_data):
	ticket = f"{customer_type[:1].upper()}{uuid.uuid4().hex[:4].upper()}"
	with db_connection() as connection:
		connection.execute(
			"""
			INSERT INTO queue_entries
			(ticket, customer_type, full_name, email, phone, section,
			 student_id, grade_level, status, created_at)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Waiting', ?)
			""",
			(
				ticket,
				customer_type,
				form_data["full_name"],
				form_data["email"],
				form_data["phone"],
				form_data.get("section"),
				form_data.get("student_id"),
				form_data.get("grade_level"),
				datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			),
		)
	return ticket


def get_entries(customer_type=None, status=None):
	query = "SELECT * FROM queue_entries"
	filters = []
	values = []
	if customer_type:
		filters.append("customer_type = ?")
		values.append(customer_type)
	if status:
		filters.append("status = ?")
		values.append(status)
	if filters:
		query += " WHERE " + " AND ".join(filters)
	query += " ORDER BY id ASC"
	with db_connection() as connection:
		return connection.execute(query, values).fetchall()


def update_status(entry_id, status):
	with db_connection() as connection:
		connection.execute("UPDATE queue_entries SET status = ? WHERE id = ?", (status, entry_id))


def make_qr_image(url):
	image = qrcode.make(url)
	output = io.BytesIO()
	image.save(output, format="PNG")
	return output.getvalue()


def app_url(path):
	base_url = os.environ.get("PICXELLENS_PUBLIC_URL", "http://localhost:8501")
	return f"{base_url.rstrip('/')}/?view={path}"


def inject_styles():
	st.markdown(
		"""
		<style>
		@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
		:root { --ink:#17221f; --muted:#6b7772; --paper:#f5f7f2; --lime:#d5f25d; --coral:#ff765f; --line:#dfe6dc; }
		.stApp { background:var(--paper); color:var(--ink); font-family:'DM Sans', sans-serif; }
		h1,h2,h3 { font-family:'Space Grotesk', sans-serif !important; letter-spacing:0 !important; color:var(--ink); }
		.brand { font:700 28px 'Space Grotesk'; letter-spacing:0; color:var(--ink); }
		.eyebrow { color:var(--coral); font-size:12px; font-weight:700; letter-spacing:1.8px; text-transform:uppercase; }
		.hero { padding:28px 0 18px; border-bottom:1px solid var(--line); margin-bottom:24px; }
		.hero h1 { font-size:42px; line-height:1.04; margin:8px 0; }
		.hero p { color:var(--muted); max-width:620px; font-size:16px; }
		.choice { min-height:210px; padding:28px; border:1px solid var(--line); border-radius:8px; background:#fff; }
		.choice.student { background:var(--lime); border-color:var(--lime); }
		.choice h2 { margin:12px 0 8px; font-size:27px; }
		.choice p { color:#56615b; min-height:46px; }
		.qr-card { background:#fff; border:1px solid var(--line); border-radius:8px; padding:22px; text-align:center; }
		.ticket { font:700 38px 'Space Grotesk'; color:var(--coral); }
		[data-testid='stSidebar'] { background:#17221f; }
		[data-testid='stSidebar'] * { color:#f5f7f2; }
		[data-testid='stSidebar'] .stRadio label { padding:9px 4px; }
		div[data-testid='stMetric'] { background:#fff; border:1px solid var(--line); border-radius:8px; padding:14px; }
		.entry { border:1px solid var(--line); border-radius:8px; background:#fff; padding:16px; margin:8px 0; }
		</style>
		""",
		unsafe_allow_html=True,
	)


def render_customer_form(customer_type):
	is_student = customer_type == "Student"
	st.markdown(f"<div class='eyebrow'>{APP_NAME} intake</div>", unsafe_allow_html=True)
	st.title("Join the photo queue")
	st.caption("Complete the form once. Staff will call your ticket when it is your turn.")
	with st.form(f"{customer_type.lower()}_form"):
		full_name = st.text_input("Full name *")
		email = st.text_input("Gmail or school Gmail *")
		phone = st.text_input("Phone number *")
		section = student_id = grade_level = ""
		if is_student:
			section = st.text_input("Section *", placeholder="e.g. STEM 12-A")
			student_id = st.text_input("Student ID *")
			grade_level = st.text_input("Grade or year level *", placeholder="e.g. Grade 12")
		submitted = st.form_submit_button("Get my queue number", type="primary", use_container_width=True)
	if submitted:
		required = [full_name, email, phone]
		if is_student:
			required += [section, student_id, grade_level]
		if not all(value.strip() for value in required):
			st.error("Please complete all required fields.")
			return
		ticket = add_queue_entry(
			customer_type,
			{"full_name": full_name.strip(), "email": email.strip(), "phone": phone.strip(),
			 "section": section.strip(), "student_id": student_id.strip(), "grade_level": grade_level.strip()},
		)
		st.success("You are now in the queue.")
		st.markdown(f"<div class='qr-card'><div>Your ticket number</div><div class='ticket'>{ticket}</div><div>Please wait for staff to call you.</div></div>", unsafe_allow_html=True)


def render_home():
	st.markdown(f"<div class='brand'>{APP_NAME}</div><div class='hero'><div class='eyebrow'>photo shop queue</div><h1>Choose your visit type.</h1><p>Scan the matching QR code or open a form to join the queue in under a minute.</p></div>", unsafe_allow_html=True)
	columns = st.columns(2, gap="large")
	cards = [("Student", "Student intake", "Section-based queue for school customers.", "student"), ("Walk-in", "Walk-in intake", "Quick queue entry for regular customers.", "walkin")]
	for column, (label, title, description, css_class) in zip(columns, cards):
		with column:
			st.markdown(f"<div class='choice {css_class}'><div class='eyebrow'>{label}</div><h2>{title}</h2><p>{description}</p></div>", unsafe_allow_html=True)
			st.link_button(f"Open {label} form", f"?view={css_class}", use_container_width=True)
			st.image(make_qr_image(app_url(css_class)), width=170)
			st.caption("Scan this QR code")


def render_queue(customer_type=None):
	label = customer_type or "All customers"
	st.markdown(f"<div class='eyebrow'>Staff view / {label}</div>", unsafe_allow_html=True)
	st.title("Queue desk")
	entries = get_entries(customer_type, "Waiting")
	all_entries = get_entries(customer_type)
	metrics = st.columns(3)
	metrics[0].metric("Waiting", len(entries))
	metrics[1].metric("Students", len([entry for entry in get_entries("Student", "Waiting")]))
	metrics[2].metric("Completed today", len([entry for entry in all_entries if entry["status"] == "Done"]))
	st.divider()
	if not entries:
		st.info("No customers are waiting right now.")
		return
	for position, entry in enumerate(entries, 1):
		with st.container(border=True):
			left, middle, right = st.columns([1, 3, 1])
			left.markdown(f"### #{position}<br><span class='ticket'>{entry['ticket']}</span>", unsafe_allow_html=True)
			details = f"**{entry['full_name']}**  \n{entry['email']} · {entry['phone']}"
			if entry["customer_type"] == "Student":
				details += f"  \nSection: **{entry['section']}** · {entry['grade_level']} · ID: {entry['student_id']}"
			middle.markdown(details)
			if right.button("Call next", key=f"call_{entry['id']}", use_container_width=True):
				update_status(entry["id"], "Serving")
				st.rerun()
	serving = get_entries(customer_type, "Serving")
	if serving:
		st.subheader("Currently serving")
		for entry in serving:
			st.info(f"{entry['ticket']} · {entry['full_name']}")
			if st.button("Mark done", key=f"done_{entry['id']}"):
				update_status(entry["id"], "Done")
				st.rerun()


def render_qr_codes():
	st.markdown("<div class='eyebrow'>Staff view / customer access</div>", unsafe_allow_html=True)
	st.title("Customer QR codes")
	st.caption("Print or display these codes at the counter. Set PICXELLENS_PUBLIC_URL to the computer's LAN address when customers use phones on the same network.")
	columns = st.columns(2, gap="large")
	for column, (label, path) in zip(columns, [("Student", "student"), ("Walk-in", "walkin")]):
		with column:
			st.markdown(f"### {label}")
			st.image(make_qr_image(app_url(path)), width=280)
			st.code(app_url(path), language=None)


def render_staff():
	st.sidebar.markdown(f"<div class='brand' style='color:#d5f25d'>{APP_NAME}</div>", unsafe_allow_html=True)
	st.sidebar.caption("STAFF DESK")
	view = st.sidebar.radio("Navigate", ["All queue", "Students", "Walk-ins", "QR codes"], label_visibility="collapsed")
	if view == "All queue":
		render_queue()
	elif view == "Students":
		render_queue("Student")
	elif view == "Walk-ins":
		render_queue("Walk-in")
	else:
		render_qr_codes()


initialize_database()
inject_styles()
view = st.query_params.get("view", "staff")
if view == "student":
	render_customer_form("Student")
elif view == "walkin":
	render_customer_form("Walk-in")
else:
	render_staff()
