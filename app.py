import streamlit as st
import time
import os
import gc
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Bulk Subscriber & Mail Monitor", layout="wide")
st.title("Universal Bulk Subscriber with Live Mail Monitor")

# Session state setup
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "submission_log" not in st.session_state:
    st.session_state.submission_log = {}  # {domain: submit_timestamp}
if "received_mails" not in st.session_state:
    st.session_state.received_mails = []
if "failed_list" not in st.session_state:
    st.session_state.failed_list = []

# Inputs Section
col_in1, col_in2 = st.columns(2)
with col_in1:
    user_email = st.text_input("Yahoo Email Address:", placeholder="example@yahoo.com")
    domains_input = st.text_area("Bulk Domains / URLs (Line by line):", placeholder="https://bellalab.sk\nhttps://cohopte.com")
with col_in2:
    yahoo_app_pass = st.text_input("Yahoo App Password (16-char code):", type="password", help="Yahoo Security Settings-la Generate App Password create pannunga")
    st.caption("Direct Yahoo password podaatheenga. Yahoo Security > Generate App Password create panni inga paste pannunga.")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

def check_yahoo_mail(user, app_password, target_domains, start_time):
    """Yahoo Inbox matrum Spam folders-a check panni domain match aana delay calculate pannum"""
    results = []
    try:
        mail_client = imaplib.IMAP4_SSL("imap.mail.yahoo.com")
        mail_client.login(user, app_password)

        for folder in ["INBOX", "Bulk"]:
            mail_client.select(folder)
            status, messages = mail_client.search(None, "UNSEEN")
            if status != "OK":
                continue

            msg_ids = messages[0].split()
            for msg_id in msg_ids[-10:]:  # Last 10 unread mails check pannum
                res, data = mail_client.fetch(msg_id, "(RFC822)")
                for response_part in data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        raw_subj = msg.get("Subject", "")
                        decoded_subj = decode_header(raw_subj)[0]
                        subject = decoded_subj[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(decoded_subj[1] if decoded_subj[1] else "utf-8", errors="ignore")
                        from_addr = msg.get("From", "")

                        # Matching domain check
                        for d in target_domains:
                            clean_d = d.replace("https://", "").replace("http://", "").split("/")[0].lower()
                            if clean_d in from_addr.lower() or clean_d in subject.lower():
                                delay_sec = round(time.time() - start_time, 1)
                                delay_str = f"{delay_sec}s" if delay_sec < 60 else f"{round(delay_sec/60, 1)}m"
                                results.append({
                                    "Domain": d,
                                    "From": from_addr,
                                    "Subject": subject,
                                    "Folder": folder,
                                    "Delay Time": delay_str,
                                    "Status": "✅ Received"
                                })
        mail_client.logout()
    except Exception:
        pass
    return results

# Controls
c_b1, c_b2, c_b3 = st.columns([1.5, 1.5, 4])
with c_b1:
    if st.button("▶️ Start Subscription & Live Tracker"):
        if not user_email or not urls:
            st.error("Email matrum Domains list compulsory da!")
        else:
            st.session_state.is_running = True
with c_b2:
    if st.button("⏹️ Stop Process"):
        st.session_state.is_running = False
with c_b3:
    if st.button("🔄 Reset All"):
        st.session_state.current_index = 0
        st.session_state.is_running = False
        st.session_state.submission_log = {}
        st.session_state.received_mails = []
        st.session_state.failed_list = []
        st.rerun()

status_box = st.empty()
progress_bar = st.progress(0)

# Automation & Live Listener Loop
if st.session_state.is_running and urls:
    total_urls = len(urls)

    browser_args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-http2",
        "--ignore-certificate-errors"
    ]

    while st.session_state.current_index < total_urls and st.session_state.is_running:
        idx = st.session_state.current_index
        raw_url = urls[idx]
        url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

        status_box.info(f"Processing ({idx + 1}/{total_urls}): {url}")
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

                # Form auto-fill & direct enter
                email_box = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
                if email_box.count() > 0:
                    email_box.fill(user_email, timeout=2500)
                    time.sleep(0.5)
                    email_box.press("Enter")
                    time.sleep(2)

                st.session_state.submission_log[url] = submit_time
                context.close()
                browser.close()

        except Exception as e:
            st.session_state.failed_list.append((url, str(e)[:30]))

        # App Password kuduthurundha udane Yahoo inbox check pannum
        if yahoo_app_pass:
            found_mails = check_yahoo_mail(user_email, yahoo_app_pass, list(st.session_state.submission_log.keys()), submit_time)
            for m in found_mails:
                if not any(x["Domain"] == m["Domain"] for x in st.session_state.received_mails):
                    st.session_state.received_mails.append(m)

        gc.collect()
        st.session_state.current_index += 1
        time.sleep(2)

    if st.session_state.current_index >= total_urls:
        status_box.success("Bulk subscriptions complete aaiduchu!")
        st.session_state.is_running = False

# Live Monitoring Dashboard UI
st.divider()
st.subheader("📬 Live Mail Monitor Dashboard")

col_d1, col_d2 = st.columns([3, 2])

with col_d1:
    st.markdown("#### ✅ Received Mails Status")
    if st.session_state.received_mails:
        st.dataframe(st.session_state.received_mails, use_container_width=True)
    else:
        st.info("Innum mails receive aagala / Background-la check pannittu iruku...")

with col_d2:
    st.markdown("#### ❌ Failed / Unreachable Sites")
    for u, err in st.session_state.failed_list:
        st.write(f"- {u} ({err})")
