import streamlit as st
import time
import os
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber (Live View)", layout="wide")
st.title("Universal Bulk Subscriber - Live Screen Stream")

@st.cache_resource
def install_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception:
        pass

install_browsers()

# State variables
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "success_list" not in st.session_state:
    st.session_state.success_list = []
if "failed_list" not in st.session_state:
    st.session_state.failed_list = []

email = st.text_input("Enter Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Bulk Domains / URLs (Line by line):", placeholder="https://bellalab.sk\nhttps://cohopte.com")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start Live Automation"):
        if not email or not urls:
            st.error("Email mattu Domains compulsory!")
        else:
            st.session_state.is_running = True

with col_b2:
    if st.button("⏹️ Stop / Pause"):
        st.session_state.is_running = False

with col_b3:
    if st.button("🔄 Reset All"):
        st.session_state.current_index = 0
        st.session_state.is_running = False
        st.session_state.success_list = []
        st.session_state.failed_list = []
        st.rerun()

st.divider()

# Live Monitor UI Layout
st.subheader("📺 Live Browser Monitor")
live_status = st.empty()
live_image = st.empty()
progress_bar = st.progress(0)

browser_args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-http2",
    "--ignore-certificate-errors",
    "--disable-blink-features=AutomationControlled"
]

def update_live_screen(page, status_msg):
    live_status.info(status_msg)
    try:
        img_bytes = page.screenshot()
        live_image.image(img_bytes, caption=status_msg, use_column_width=True)
    except Exception:
        pass
    time.sleep(1)

# Automation Loop with Live Visual Feed
if st.session_state.is_running and urls:
    total_urls = len(urls)

    while st.session_state.current_index < total_urls and st.session_state.is_running:
        idx = st.session_state.current_index
        raw_url = urls[idx]
        url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

        progress_bar.progress((idx + 1) / total_urls)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=browser_args)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    ignore_https_errors=True
                )
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page = context.new_page()

                # 1. Loading website live
                update_live_screen(page, f"Step 1: Opening {url}...")
                page.goto(url, timeout=25000, wait_until="commit")
                time.sleep(3)
                update_live_screen(page, f"Step 2: Loaded page successfully: {url}")

                # 2. Human / Account icon check
                try:
                    human_icon = page.locator("a[href*='account' i], a[href*='login' i], a[href*='registr' i], svg[class*='user' i]").first
                    if human_icon.count() > 0 and human_icon.is_visible():
                        update_live_screen(page, "Step 3: Account/Register icon click maaduttide...")
                        human_icon.click(timeout=2000)
                        time.sleep(2)
                except Exception:
                    pass

                # 3. Filling form
                name_box = page.locator("input[placeholder*='name' i], input[name*='name' i], input[id*='name' i], input[placeholder*='meno' i]").first
                if name_box.count() > 0 and name_box.is_visible():
                    name_box.fill(fake.first_name(), timeout=1500)

                email_box = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i], input[id*='email' i]").first
                if email_box.count() > 0 and email_box.is_visible():
                    email_box.fill(email, timeout=2000)
                    update_live_screen(page, f"Step 4: Email address fill aayithu ({email})")

                    # Checkbox
                    try:
                        cb = page.locator("input[type='checkbox']").first
                        if cb.count() > 0:
                            cb.check(force=True, timeout=1000)
                    except Exception:
                        pass

                    # Submit / Enter
                    update_live_screen(page, "Step 5: Form submit maadalu Enter press maaduttide...")
                    btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Subscribe'), button:has-text('ZÍSKAŤ')").first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click(timeout=2000)
                    else:
                        email_box.press("Enter")

                    time.sleep(3)
                    update_live_screen(page, "Step 6: Submitted! Result screen check maaduttide...")

                    st.session_state.success_list.append(url)
                else:
                    update_live_screen(page, "Form field sigalilla (No email input).")
                    st.session_state.failed_list.append((url, "Email input box missing"))

                context.close()
                browser.close()

        except Exception as e:
            st.session_state.failed_list.append((url, str(e)[:30]))

        st.session_state.current_index += 1
        time.sleep(1)

    if st.session_state.current_index >= total_urls:
        live_status.success("Ellavu mugidide! Complete process finished.")
        st.session_state.is_running = False

# Summary Section
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader(f"✅ Subscribed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed / Skipped ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
