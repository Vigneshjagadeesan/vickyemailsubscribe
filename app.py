import streamlit as st
import time
import os
import gc
import imaplib
import email
from email.header import decode_header
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber & Live Multi-Mail Monitor", layout="wide")
st.title("Universal Multi-Account Bulk Subscriber & Live Tracker")

# Session State Setup
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "submission_log" not in st.session_state:
    st.session_state.submission_log = {}
if "received_mails" not in st.session_state:
    st.session_state.received_mails = []
if "failed_list" not in st.session_state:
    st.session_state.failed_list = []

# Left side: Domains (Common for everyone) | Right side: Individual Provider Tabs
col_left, col_right = st.columns([1.2, 1.8])

with col_left:
    st.subheader("🌐 Target Websites")
    domains_input = st.text_area(
        "Enter Bulk Domains (Line by line):",
        placeholder="https://bellalab.sk\nhttps://cohopte.com\nhttps://example.com",
        height=260
    )
    urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

with col_right:
    st.subheader("🔐 Choose Email Provider")
    tab_yahoo, tab_outlook, tab_gmail, tab_custom = st.tabs(["🟣 Yahoo Mail", "🔵 Outlook / Hotmail", "🔴 Gmail", "⚪ Custom Domain"])

    active_email = ""
    active_password = ""
    imap_server = ""
    spam_folder_name = "Bulk"

    with tab_yahoo:
        st.caption("Yahoo mail tracking & auto-subscription")
        y_email = st.text_input("Yahoo Email Address:", key="y_email", placeholder="username@yahoo.com")
        y_pass = st.text_input("Yahoo App Password (16-char):", type="password", key="y_pass")
        if y_email and y_pass:
            active_email = y_email
            active_password = y_pass
            imap_server = "imap.mail.yahoo.com"
            spam_folder_name = "Bulk"

    with tab_outlook:
        st.caption("Outlook, Hotmail & Live accounts")
        o_email = st.text_input("Outlook/Hotmail Address:", key="o_email", placeholder="username@outlook.com")
        o_pass = st.text_input("Outlook App Password:", type="password", key="o_pass")
        if o_email and o_pass:
            active_email = o_email
            active_password = o_pass
            imap_server = "outlook.office365.com"
            spam_folder_name = "Junk"

    with tab_gmail:
        st.caption("Gmail accounts (Requires 2FA App Password)")
        g_email = st.text_input("Gmail Address:", key="g_email", placeholder="username@gmail.com")
        g_pass = st.text_input("Gmail 16-Digit App Password:", type="password", key="g_pass")
        if g_email and g_pass:
            active_email = g_email
            active_password = g_pass
            imap_server = "imap.gmail.com"
            spam_folder_name = "[Gmail]/Spam"

    with tab_custom:
        st.caption("Custom Domain / Business Webmail")
        c_email = st.text_input("Custom Email Address:", key="c_email", placeholder="admin@domain.com")
        c_pass = st.text_input("Mailbox Password:", type="password", key="c_pass")
        c_host = st.text_input("Custom IMAP Host:", key="c_host", placeholder="mail.yourdomain.com")
        if c_email and c_pass:
            active_email = c_email
            active_password = c_pass
            imap_server = c_host if c_host else f"mail.{c_email.split('@')[-1]}"
            spam_folder_name = "Junk"

# IMAP Check Function
def check_inbox_and_spam(server_host, user, app_pass, target_domains, start_time, spam_name):
    results = []
    try:
        mail_client = imaplib.IMAP4_SSL(server_host, 993)
        mail_client.login(user, app_pass)

        folders_to_check = ["INBOX", spam_name]
        for folder in folders_to_check:
            try:
                status, _ = mail_client.select(f'"{folder}"')
                if status != "OK":
                    continue
            except Exception:
                continue

            status, messages = mail_client.search(None, "UNSEEN")
            if status != "OK" or not messages[0]:
                continue

            msg_ids = messages[0].split()
            for msg_id in msg_ids[-10:]:
                res, data = mail_client.fetch(msg_id, "(RFC822)")
                for part in data:
                    if isinstance(part, tuple):
                        msg = email.message_from_bytes(part[1])
                        raw_sub = msg.get("Subject", "")
                        dec_sub = decode_header(raw_sub)[0]
                        subject = dec_sub[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(dec_sub[1] if dec_sub[1] else "utf-8", errors="ignore")
                        from_addr = msg.get("From", "")

                        for d in target_domains:
                            clean_d = d.replace("https://", "").replace("http://", "").split("/")[0].lower()
                            if clean_d in from_addr.lower() or clean_d in subject.lower():
                                delay_sec = round(time.time() - start_time, 1)
                                delay_str = f"{delay_sec}s" if delay_sec < 60 else f"{round(delay_sec/60, 1)}m"
                                results.append({
                                    "Domain": d,
                                    "Sender": from_addr,
                                    "Subject": subject,
                                    "Folder": folder,
                                    "Delay": delay_str,
                                    "Status": "✅ Received"
                                })
        mail_client.logout()
    except Exception:
        pass
    return results

# Process Buttons
col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start Subscription & Live Tracking"):
        if not active_email or not urls:
            st.error("Select panna tab-la Email address matrum Left side Domains compulsory da!")
        else:
            st.session_state.is_running = True

with col_b2:
    if st.button("⏹️ Stop Process"):
        st.session_state.is_running = False

with col_b3:
    if st.button("🔄 Reset All"):
        st.session_state.current_index = 0
        st.session_state.is_running = False
        st.session_state.submission_log = {}
        st.session_state.received_mails = []
        st.session_state.failed_list = []
        st.rerun()

status_box = st.empty()
progress_bar = st.progress(0)

browser_args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-http2",
    "--ignore-certificate-errors"
]

# Subscription Engine
if st.session_state.is_running and urls and active_email:
    total_urls = len(urls)

    while st.session_state.current_index < total_urls and st.session_state.is_running:
        idx = st.session_state.current_index
        raw_url = urls[idx]
        url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

        status_box.info(f"Targeting ({idx + 1}/{total_urls}): {url} | Using: {active_email}")
        progress_bar.progress((idx + 1) / total_urls)
        submit_time = time.time()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=browser_args)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    ignore_https_errors=True
                )
                page = context.new_page()
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

                page.goto(url, timeout=25000, wait_until="commit")
                time.sleep(2)

                # Form input autofill & Enter
                email_box = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
                if email_box.count() > 0:
                    email_box.fill(active_email, timeout=2500)
                    time.sleep(0.5)
                    email_box.press("Enter")
                    time.sleep(2)

                st.session_state.submission_log[url] = submit_time
                context.close()
                browser.close()

        except Exception as e:
            st.session_state.failed_list.append((url, str(e)[:30]))

        # Instant Mail Monitor Check
        if active_password and imap_server:
            incoming = check_inbox_and_spam(imap_server, active_email, active_password, list(st.session_state.submission_log.keys()), submit_time, spam_folder_name)
            for item in incoming:
                if not any(x["Domain"] == item["Domain"] for x in st.session_state.received_mails):
                    st.session_state.received_mails.append(item)

        gc.collect()
        st.session_state.current_index += 1
        time.sleep(2)

    if st.session_state.current_index >= total_urls:
        status_box.success("Ella websites-kum process mudinjiduchu!")
        st.session_state.is_running = False

# Live Monitoring Display
st.divider()
st.subheader("📊 Live Delivery Tracking Dashboard")

c_log1, c_log2 = st.columns([3, 2])
with c_log1:
    st.markdown("#### 📬 Received Newsletters / Confirmation Emails")
    if st.session_state.received_mails:
        st.dataframe(st.session_state.received_mails, use_container_width=True)
    else:
        st.info("Innum mails receive aagala / Background-la monitoring nadakudhu...")

with c_log2:
    st.markdown("#### ❌ Skipped / Unreachable Sites")
    for u, err in st.session_state.failed_list:
        st.write(f"- {u} ({err})")
