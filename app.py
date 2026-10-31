import streamlit as st
import time
import os
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber (Smart Human/Register)", layout="wide")
st.title("Universal Bulk Subscriber (Human/Account & OTP/CAPTCHA Solver)")

@st.cache_resource
def install_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception:
        pass

install_browsers()

# Session State
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "success_list" not in st.session_state:
    st.session_state.success_list = []
if "failed_list" not in st.session_state:
    st.session_state.failed_list = []
if "waiting_for_user" not in st.session_state:
    st.session_state.waiting_for_user = False
if "pending_site" not in st.session_state:
    st.session_state.pending_site = None
if "pending_type" not in st.session_state:
    st.session_state.pending_type = None

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Bulk Domains / URLs (Ovoru line-kum oru domain):", placeholder="https://bellalab.sk\nhttps://cohopte.com")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start / Continue Bulk Process"):
        if not email or not urls:
            st.error("Email matrum Bulk Domains list compulsory da!")
        else:
            st.session_state.is_running = True
            st.session_state.waiting_for_user = False

with col_b2:
    if st.button("⏹️ Stop / Pause"):
        st.session_state.is_running = False

with col_b3:
    if st.button("🔄 Reset All"):
        st.session_state.current_index = 0
        st.session_state.is_running = False
        st.session_state.waiting_for_user = False
        st.session_state.pending_site = None
        st.session_state.success_list = []
        st.session_state.failed_list = []
        if os.path.exists("current_screen.png"):
            try:
                os.remove("current_screen.png")
            except Exception:
                pass
        st.rerun()

def fill_all_inputs(page, user_email):
    """Human icon click aana approm ella boxes-um safe-aa fill pannum"""
    # 1. First Name
    first_name_input = page.locator("input[placeholder*='meno' i], input[name*='firstname' i], input[id*='firstname' i], input[name*='name' i], input[placeholder*='name' i]").first
    if first_name_input.count() > 0 and first_name_input.is_visible():
        try:
            first_name_input.fill(fake.first_name(), timeout=3000)
        except Exception:
            pass

    # 2. Last Name
    last_name_input = page.locator("input[name*='lastname' i], input[id*='lastname' i], input[placeholder*='last' i]").first
    if last_name_input.count() > 0 and last_name_input.is_visible():
        try:
            last_name_input.fill(fake.last_name(), timeout=3000)
        except Exception:
            pass

    # 3. Email
    email_input = page.locator("input[type='email'], input[name*='email' i], input[id*='email' i], input[placeholder*='mail' i]").first
    if email_input.count() > 0 and email_input.is_visible():
        try:
            email_input.fill(user_email, timeout=4000)
        except Exception:
            pass

    # 4. Password
    pass_input = page.locator("input[type='password']").first
    if pass_input.count() > 0 and pass_input.is_visible():
        try:
            pass_input.fill("AutoPass@2026", timeout=3000)
        except Exception:
            pass

    # 5. Checkboxes (terms/newsletter)
    checkboxes = page.locator("input[type='checkbox']").all()
    for cb in checkboxes:
        try:
            cb.check(force=True, timeout=2000)
        except Exception:
            pass

    # 6. Submit Button
    submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Register'), button:has-text('Sign up'), button:has-text('Vytvoriť'), button:has-text('ZÍSKAŤ'), button:has-text('Subscribe')").first
    if submit_btn.count() > 0 and submit_btn.is_visible():
        try:
            submit_btn.click(timeout=4000)
            return True
        except Exception:
            pass
    elif email_input.count() > 0:
        try:
            email_input.press("Enter")
            return True
        except Exception:
            pass
    return False

browser_args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu"
]

status_box = st.empty()
progress_bar = st.progress(0)

# Main Automation Loop
if st.session_state.is_running and not st.session_state.waiting_for_user and urls:
    total_urls = len(urls)

    with sync_playwright() as p:
        while st.session_state.current_index < total_urls and st.session_state.is_running:
            idx = st.session_state.current_index
            raw_url = urls[idx]
            url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

            status_box.info(f"Processing ({idx + 1}/{total_urls}): {url}")
            progress_bar.progress((idx + 1) /
