import streamlit as st
import time
import os
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber", layout="wide")
st.title("Universal Bulk Subscriber (Step-by-Step Engine)")

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
if "waiting_for_user" not in st.session_state:
    st.session_state.waiting_for_user = False
if "pending_site" not in st.session_state:
    st.session_state.pending_site = None
if "pending_type" not in st.session_state:
    st.session_state.pending_type = None

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Domains / URLs (Oru line-ku oru domain):", placeholder="https://bellalab.sk\nhttps://cohopte.com")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start / Continue Process"):
        if not email or not urls:
            st.error("Email matrum Domains compulsory da!")
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

def fill_form_and_press_enter(page, user_email):
    # Name fields auto-fill
    try:
        name_box = page.locator("input[placeholder*='name' i], input[name*='name' i], input[id*='name' i], input[placeholder*='meno' i]").first
        if name_box.count() > 0 and name_box.is_visible():
            name_box.fill(fake.first_name(), timeout=2000)
    except Exception:
        pass

    # Password iruntha auto-fill
    try:
        pwd_box = page.locator("input[type='password']").first
        if pwd_box.count() > 0 and pwd_box.is_visible():
            pwd_box.fill("AutoSecure@2026", timeout=2000)
    except Exception:
        pass

    # Checkboxes tick panrom
    try:
        boxes = page.locator("input[type='checkbox']").all()
        for b in boxes:
            try:
                b.check(force=True, timeout=1000)
            except Exception:
                pass
    except Exception:
        pass

    # Button thedama direct-aa email fill panni ENTER adikirom
    try:
        email_box = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i], input[id*='email' i]").first
        if email_box.count() > 0 and email_box.is_visible():
            email_box.fill(user_email, timeout=3000)
            time.sleep(0.5)
            email_box.press("Enter")
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

# Main Step-by-Step Loop
if st.session_state.is_running and not st.session_state.waiting_for_user and urls:
    total_urls = len(urls)

    while st.session_state.current_index < total_urls and st.session_state.is_running:
        idx = st.session_state.current_index
        raw_url = urls[idx]
        url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

        status_box.info(f"Processing ({idx + 1}/{total_urls}): {url}")
        progress_bar.progress((idx + 1) / total_urls)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=browser_args)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    ignore_https_errors=True
                )
                page = context.new_page()

                # Site porumaiya load aaga 25s timeout
                page.goto(url, timeout=25000, wait_until="domcontentloaded")
                time.sleep(3)

                # Human/Account icon iruntha click
                try:
                    human_icon = page.locator("a[href*='account' i], a[href*='login' i], a[href*='registr' i], svg[class*='user' i]").first
                    if human_icon.count() > 0 and human_icon.is_visible():
                        human_icon.click(timeout=2000)
                        time.sleep(2)
                except Exception:
                    pass

                # Fill & Direct Enter
                fill_form_and_press_enter(page, email)
                time.sleep(4)

                # CAPTCHA / OTP Check
                is_captcha = False
                is_otp = False
                try:
                    is_captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], text=/robot|captcha|verification/i").count() > 0
                    is_otp = page.locator("input[name*='otp' i], input[name*='code' i], input[placeholder*='code' i], text=/verification code|enter otp|kód/i").count() > 0
                except Exception:
                    pass

                # Skip aagama UI-la pause panni nikkum
                if is_captcha or is_otp:
                    page.screenshot(path="current_screen.png")
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = url
                    st.session_state.pending_type = "OTP" if is_otp else "CAPTCHA"
                    context.close()
                    browser.close()
                    st.rerun()

                st.session_state.success_list.append(url)
                context.close()
                browser.close()

        except Exception as e:
            st.session_state.failed_list.append((url, str(e)[:35]))

        st.session_state.current_index += 1
        time.sleep(2)  # Sites block pannama iruka chinna gap

    if st.session_state.current_index >= total_urls:
        status_box.success("Ella websites-um mudinjiduchu!")
        st.session_state.is_running = False

# Screen-la OTP/CAPTCHA varumpothu input vaanga
if st.session_state.waiting_for_user and os.path.exists("current_screen.png"):
    st.divider()
    st.subheader(f"⚠️ Action Required: {st.session_state.pending_site}")
    st.image("current_screen.png", caption="Current Website View")

    user_code = st.text_input(f"Inga {st.session_state.pending_type} code type pannunga:")

    c_sub1, c_sub2 = st.columns([2, 5])
    with c_sub1:
        if st.button("Submit & Next Site-ku Po"):
            st.session_state.success_list.append(st.session_state.pending_site)
            st.session_state.current_index += 1
            st.session_state.waiting_for_user = False
            st.session_state.pending_site = None
            st.session_state.is_running = True
            st.rerun()
    with c_sub2:
        if st.button("Skip Pannu"):
            st.session_state.failed_list.append((st.session_state.pending_site, "Skipped by user"))
            st.session_state.current_index += 1
            st.session_state.waiting_for_user = False
            st.session_state.pending_site = None
            st.session_state.is_running = True
            st.rerun()

# Results
c1, c2 = st.columns(2)
with c1:
    st.subheader(f"✅ Subscribed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed / Skipped ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
