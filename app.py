import streamlit as st
import time
import os
import gc
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber", layout="wide")
st.title("Universal Bulk Subscriber (Protocol & Anti-Crash Fixed)")

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
domains_input = st.text_area("Enter Bulk Domains / URLs (Oru line-ku oru domain):", placeholder="https://bellalab.sk\nhttps://cohopte.com")

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
    # Name auto-fill
    try:
        name_box = page.locator("input[placeholder*='name' i], input[name*='name' i], input[id*='name' i], input[placeholder*='meno' i]").first
        if name_box.count() > 0 and name_box.is_visible():
            name_box.fill(fake.first_name(), timeout=1500)
    except Exception:
        pass

    # Password auto-fill
    try:
        pwd_box = page.locator("input[type='password']").first
        if pwd_box.count() > 0 and pwd_box.is_visible():
            pwd_box.fill("AutoSecure@2026", timeout=1500)
    except Exception:
        pass

    # Checkboxes auto-tick
    try:
        boxes = page.locator("input[type='checkbox']").all()
        for b in boxes:
            try:
                b.check(force=True, timeout=1000)
            except Exception:
                pass
    except Exception:
        pass

    # Email & Submit
    try:
        email_box = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i], input[id*='email' i]").first
        if email_box.count() > 0 and email_box.is_visible():
            email_box.fill(user_email, timeout=2500)
            time.sleep(0.5)
            
            # Submit button try pannum, illana Enter adikkum
            btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Subscribe'), button:has-text('ZÍSKAŤ')").first
            if btn.count() > 0 and btn.is_visible():
                btn.click(timeout=2000)
            else:
                email_box.press("Enter")
            return True
    except Exception:
        pass

    return False

# ERR_HTTP2_PROTOCOL_ERROR matrum crash thadukura optimized flags
browser_args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-http2",  # Protocol error fix
    "--ignore-certificate-errors",
    "--disable-blink-features=AutomationControlled"
]

status_box = st.empty()
progress_bar = st.progress(0)

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
                
                # Bot fingerprint bypass
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page = context.new_page()

                # Memory save panna images block
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

                # commit wait - Connection reset aaguradhukulla content load panna
                page.goto(url, timeout=25000, wait_until="commit")
                time.sleep(3)

                # Human / Account icon click
                try:
                    human_icon = page.locator("a[href*='account' i], a[href*='login' i], a[href*='registr' i], svg[class*='user' i]").first
                    if human_icon.count() > 0 and human_icon.is_visible():
                        human_icon.click(timeout=2000)
                        time.sleep(2)
                except Exception:
                    pass

                # Form fill & submit
                fill_form_and_press_enter(page, email)
                time.sleep(3)

                # CAPTCHA / OTP Check
                is_captcha = False
                is_otp = False
                try:
                    is_captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], text=/robot|captcha|verification/i").count() > 0
                    is_otp = page.locator("input[name*='otp' i], input[name*='code' i], input[placeholder*='code' i], text=/verification code|enter otp|kód/i").count() > 0
                except Exception:
                    pass

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
            err_str = str(e)
            if "ERR_HTTP2" in err_str or "CONNECTION_RESET" in err_str:
                st.session_state.failed_list.append((url, "Site firewall blocked connection"))
            elif "closed" in err_str or "Target" in err_str:
                st.session_state.failed_list.append((url, "Memory Timeout (Skipped)"))
            else:
                st.session_state.failed_list.append((url, err_str[:30]))

        gc.collect()
        st.session_state.current_index += 1
        time.sleep(2)

    if st.session_state.current_index >= total_urls:
        status_box.success("Ella websites-um mudinjiduchu!")
        st.session_state.is_running = False

# Screen verification prompt
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

# Results Section
c1, c2 = st.columns(2)
with c1:
    st.subheader(f"✅ Subscribed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed / Skipped ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
