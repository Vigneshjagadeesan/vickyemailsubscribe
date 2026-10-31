import streamlit as st
import time
import gc
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber", layout="wide")
st.title("Universal Auto-Subscriber (Streamlit Cloud Safe)")

# Browser binaries install check
@st.cache_resource
def install_playwright_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.caption(f"Install check: {e}")

install_playwright_browsers()

# State management
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "success_list" not in st.session_state:
    st.session_state.success_list = []
if "captcha_list" not in st.session_state:
    st.session_state.captcha_list = []
if "otp_list" not in st.session_state:
    st.session_state.otp_list = []
if "failed_list" not in st.session_state:
    st.session_state.failed_list = []

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Domains / URLs (Line by line):", placeholder="https://bellalab.sk")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start / Continue"):
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
        st.session_state.captcha_list = []
        st.session_state.otp_list = []
        st.session_state.failed_list = []
        st.rerun()

def check_captcha(page):
    try:
        captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], iframe[src*='turnstile' i], div[class*='captcha' i], div[id*='captcha' i], text=/robot|captcha|human verification/i")
        return captcha.count() > 0
    except Exception:
        return False

def check_otp(page):
    try:
        otp = page.locator("input[name*='otp' i], input[id*='otp' i], input[placeholder*='code' i], input[name*='code' i], text=/verification code|enter otp|kód/i")
        return otp.count() > 0
    except Exception:
        return False

def fill_and_submit(scope, user_email):
    """Broad CSS and generic attribute matcher for newsletter forms"""
    submitted = False
    try:
        # 1. Fill Name if available
        name_input = scope.locator("input[placeholder*='meno' i], input[name*='name' i], input[placeholder*='name' i], input[id*='name' i]").first
        if name_input.count() > 0 and name_input.is_visible():
            name_input.fill(fake.first_name())

        # 2. Fill Email (Multiple fallbacks)
        email_input = scope.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i], input[id*='email' i]").first
        if email_input.count() > 0 and email_input.is_visible():
            email_input.fill(user_email)
            time.sleep(0.5)

            # 3. Fill Password if prompted
            pass_input = scope.locator("input[type='password']").first
            if pass_input.count() > 0 and pass_input.is_visible():
                pass_input.fill("AutoPass@2026")

            # 4. Check consent/newsletter checkboxes
            checkboxes = scope.locator("input[type='checkbox']").all()
            for cb in checkboxes:
                try:
                    cb.check(force=True)
                except Exception:
                    pass

            # 5. Click Subscribe/Submit
            submit_btn = scope.locator("button[type='submit'], input[type='submit'], button:has-text('ZÍSKAŤ'), button:has-text('Zaregistrovať'), button:has-text('Subscribe'), button:has-text('Sign Up'), button:has-text('Prihlásiť'), button:has-text('Odoslať')").first
            if submit_btn.count() > 0 and submit_btn.is_visible():
                submit_btn.click(timeout=3000)
                submitted = True
            else:
                email_input.press("Enter")
                submitted = True
    except Exception:
        pass
    return submitted

# Ultra-low RAM flags for Streamlit Cloud
cloud_chromium_args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
    "--no-zygote",
    "--renderer-process-limit=1"
]

status_box = st.empty()
progress_bar = st.progress(0)

if st.session_state.is_running and urls:
    total_urls = len(urls)

    with sync_playwright() as p:
        while st.session_state.current_index < total_urls and st.session_state.is_running:
            idx = st.session_state.current_index
            raw_url = urls[idx]
            url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

            status_box.info(f"Processing ({idx + 1}/{total_urls}): {url}")
            progress_bar.progress((idx + 1) / total_urls)

            browser = None
            try:
                # Launch per-domain to completely prevent RAM crashes
                browser = p.chromium.launch(headless=True, args=cloud_chromium_args)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    ignore_https_errors=True
                )
                page = context.new_page()

                # Timeout 20s - avoids hanging on slow marketing trackers
                page.goto(url, timeout=20000, wait_until="commit")
                time.sleep(3)

                # Check Captcha
                if check_captcha(page):
                    st.session_state.captcha_list.append(url)
                else:
                    success = False

                    # Priority 1: Popups / Modals
                    popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible, div[role='dialog']:visible").first
                    if popup.count() > 0:
                        if fill_and_submit(popup, email):
                            success = True
                            time.sleep(2)

                    # Priority 2: Account/User registration icons
                    if not success:
                        user_icon = page.locator("a[href*='account' i], a[href*='login' i], a[href*='prihlasenie' i], svg[class*='user' i]").first
                        if user_icon.count() > 0 and user_icon.is_visible():
                            try:
                                user_icon.click(timeout=2000)
                                time.sleep(1.5)
                                reg_btn = page.locator("a:has-text('Registr'), button:has-text('Registr'), a:has-text('Sign up')").first
                                if reg_btn.count() > 0:
                                    reg_btn.click(timeout=2000)
                                    time.sleep(1)
                                if fill_and_submit(page, email):
                                    success = True
                                    time.sleep(2)
                            except Exception:
                                pass

                    # Priority 3: Whole page / Footer form
                    if not success:
                        if fill_and_submit(page, email):
                            success = True
                            time.sleep(2)

                    # Post submission validation
                    if check_captcha(page):
                        st.session_state.captcha_list.append(url)
                    elif check_otp(page):
                        st.session_state.otp_list.append(url)
                    elif success:
                        st.session_state.success_list.append(url)
                    else:
                        st.session_state.failed_list.append((url, "No newsletter box detected"))

            except Exception as e:
                err_msg = str(e)
                if "TargetClosed" in err_msg or "closed" in err_msg:
                    st.session_state.failed_list.append((url, "RAM limit exceeded (Skipped to avoid freeze)"))
                else:
                    st.session_state.failed_list.append((url, f"Load Error: {err_msg[:30]}"))
            finally:
                if browser:
                    try:
                        browser.close()
                    except Exception:
                        pass
                # Explicit garbage collection to free Streamlit Cloud RAM
                gc.collect()

            st.session_state.current_index += 1

    if st.session_state.current_index >= total_urls:
        status_box.success("Processing completed!")
        st.session_state.is_running = False
    elif not st.session_state.is_running:
        status_box.warning(f"Paused at ({st.session_state.current_index}/{total_urls}). Click 'Start / Continue' to resume.")

# 4 Columns Display
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.subheader(f"✅ Subscribed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"🧩 CAPTCHA ({len(st.session_state.captcha_list)})")
    for item in st.session_state.captcha_list:
        st.markdown(f"- [{item}]({item})")
with c3:
    st.subheader(f"🔢 OTP Needed ({len(st.session_state.otp_list)})")
    for item in st.session_state.otp_list:
        st.markdown(f"- [{item}]({item})")
with c4:
    st.subheader(f"❌ Failed ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
