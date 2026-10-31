import streamlit as st
import time
import os
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber (Step Live View)", layout="wide")
st.title("Universal Bulk Subscriber - Live Step-by-Step Monitor")

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

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Bulk Domains / URLs (Line by line):", placeholder="https://bellalab.sk\nhttps://cohopte.com")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start Step Live Automation"):
        if not email or not urls:
            st.error("Email matrum Domains compulsory da!")
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

# Live View Screen Area
st.subheader("📺 Real-Time Screenshot Monitor")
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

def show_step(page, msg, wait_sec=2):
    live_status.info(msg)
    try:
        img_bytes = page.screenshot()
        live_image.image(img_bytes, caption=msg, use_column_width=True)
    except Exception:
        pass
    time.sleep(wait_sec)

# Step-by-Step Main Execution Loop
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

                # Step 1: Page Open panradhu
                show_step(page, f"Step 1: Website open aagudhu -> {url}", wait_sec=1)
                page.goto(url, timeout=25000, wait_until="commit")
                time.sleep(3)
                show_step(page, f"Step 2: Page load aaiduchu -> {url}", wait_sec=2)

                # Step 2: Account/Register icon irundha click
                try:
                    human_icon = page.locator("a[href*='account' i], a[href*='login' i], a[href*='registr' i], svg[class*='user' i]").first
                    if human_icon.count() > 0 and human_icon.is_visible():
                        human_icon.click(timeout=2000)
                        time.sleep(2)
                        show_step(page, "Step 3: Registration / Account open pannirukku", wait_sec=2)
                except Exception:
                    pass

                # Step 3: Name & Email auto-type
                name_box = page.locator("input[placeholder*='name' i], input[name*='name' i], input[id*='name' i], input[placeholder*='meno' i]").first
                if name_box.count() > 0 and name_box.is_visible():
                    name_box.fill(fake.first_name(), timeout=1500)

                email_box = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i], input[id*='email' i]").first
                if email_box.count() > 0 and email_box.is_visible():
                    email_box.fill(email, timeout=2000)
                    show_step(page, f"Step 4: Email fill panniyaachu ({email})", wait_sec=2)

                    # Checkbox tick
                    try:
                        cb = page.locator("input[type='checkbox']").first
                        if cb.count() > 0:
                            cb.check(force=True, timeout=1000)
                    except Exception:
                        pass

                    # Step 4: Submit / Enter Press
                    btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Subscribe'), button:has-text('ZÍSKAŤ')").first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click(timeout=2000)
                    else:
                        email_box.press("Enter")

                    # Step 5: Final Submission Result Screen
                    time.sleep(4)
                    show_step(page, f"Step 5: Submitted! Idhu {url} submit aana approm vandha screen.", wait_sec=4)

                    st.session_state.success_list.append(url)
                else:
                    show_step(page, f"Email input field kedaikala: {url}", wait_sec=2)
                    st.session_state.failed_list.append((url, "No input box"))

                context.close()
                browser.close()

        except Exception as e:
            st.session_state.failed_list.append((url, str(e)[:30]))

        # Oru domain poorthiyaana udaney adutha domain-ku move aagum
        st.session_state.current_index += 1
        time.sleep(2)

    if st.session_state.current_index >= total_urls:
        live_status.success("Ellaa domains-um poorthiyaa mudinjiduchu!")
        st.session_state.is_running = False

# Results
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader(f"✅ Processed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
