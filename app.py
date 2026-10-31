import streamlit as st
import time
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber", layout="wide")
st.title("Universal Auto-Subscriber (Pause & Resume Supported)")

@st.cache_resource
def install_playwright_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.caption(f"Browser installation check: {e}")

install_playwright_browsers()

# State variables - Browser refresh aanaalum details erase aagaama irukka
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

# Control Buttons
col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 4])
with col_btn1:
    if st.button("▶️ Start / Continue"):
        if not email or not urls:
            st.error("Email matrum Domains compulsory-aa kudunga da!")
        else:
            st.session_state.is_running = True

with col_btn2:
    if st.button("⏹️ Stop / Pause"):
        st.session_state.is_running = False

with col_btn3:
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
        captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], iframe[src*='turnstile' i], div[class*='captcha' i], text=/robot|captcha|verification/i")
        return captcha.count() > 0
    except Exception:
        return False

def check_otp(page):
    try:
        otp = page.locator("input[name*='otp' i], input[id*='otp' i], input[placeholder*='code' i], text=/verification code|enter otp|kód/i")
        return otp.count() > 0
    except Exception:
        return False

def fill_all_inputs(scope, user_email):
    filled = False
    try:
        name_input = scope.locator("input[placeholder*='meno' i], input[name*='name' i], input[placeholder*='name' i], input[id*='name' i]").first
        if name_input.count() > 0 and name_input.is_visible():
            name_input.fill(fake.first_name())

        email_input = scope.locator("input[type='email'], input[placeholder*='e-mail' i], input[name*='email' i], input[id*='email' i]").first
        if email_input.count() > 0 and email_input.is_visible():
            email_input.fill(user_email)
            filled = True

        pass_input = scope.locator("input[type='password']").first
        if pass_input.count() > 0 and pass_input.is_visible():
            pass_input.fill("Password@2026")

        checkbox = scope.locator("input[type='checkbox']").first
        if checkbox.count() > 0 and checkbox.is_visible():
            try:
                checkbox.check(force=True)
            except Exception:
                pass

        submit_btn = scope.locator("button[type='submit'], input[type='submit'], button:has-text('ZÍSKAŤ'), button:has-text('Zaregistrovať'), button:has-text('Subscribe'), button:has-text('Odoslať'), button:has-text('Prihlásiť')").first
        if submit_btn.count() > 0 and submit_btn.is_visible():
            submit_btn.click()
            return True
        elif filled:
            scope.press("Enter")
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
            subscribed = False
            try:
                browser = p.chromium.launch(headless=True, args=browser_args)
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page.goto(url, timeout=25000, wait_until="domcontentloaded")
                time.sleep(2)

                if check_captcha(page):
                    st.session_state.captcha_list.append(url)
                else:
                    popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible, div[role='dialog']:visible").first
                    if popup.count() > 0:
                        if fill_all_inputs(popup, email):
                            subscribed = True
                            time.sleep(2)

                    if not subscribed:
                        user_icon = page.locator("a[href*='account' i], a[href*='login' i], a[href*='prihlasenie' i], svg[class*='user' i]").first
                        if user_icon.count() > 0 and user_icon.is_visible():
                            try:
                                user_icon.click(timeout=3000)
                                time.sleep(2)
                                reg_tab = page.locator("a:has-text('Registr'), button:has-text('Registr'), a:has-text('Sign up')").first
                                if reg_tab.count() > 0:
                                    reg_tab.click(timeout=3000)
                                    time.sleep(1)
                                if fill_all_inputs(page, email):
                                    subscribed = True
                                    time.sleep(2)
                            except Exception:
                                pass

                    if not subscribed:
                        footer_scope = page.locator("footer, div[class*='footer' i]").first
                        scope_to_use = footer_scope if footer_scope.count() > 0 else page
                        if fill_all_inputs(scope_to_use, email):
                            subscribed = True
                            time.sleep(2)

                    if check_captcha(page):
                        st.session_state.captcha_list.append(url)
                    elif check_otp(page):
                        st.session_state.otp_list.append(url)
                    elif subscribed:
                        st.session_state.success_list.append(url)
                    else:
                        st.session_state.failed_list.append((url, "Form / Button kandupidikka mudiyala"))

            except Exception as e:
                st.session_state.failed_list.append((url, f"Error: {str(e)[:40]}"))
            finally:
                if browser:
                    try:
                        browser.close()
                    except Exception:
                        pass

            st.session_state.current_index += 1

    if st.session_state.current_index >= total_urls:
        status_box.success("Ella websites-um process aaiduchu!")
        st.session_state.is_running = False
    elif not st.session_state.is_running:
        status_box.warning(f"Process paused! ({st.session_state.current_index}/{total_urls}) mudinjirukku. Continue panna 'Start / Continue' click pannunga.")

# Output columns display
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.subheader(f"✅ Subscribed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"🧩 CAPTCHA ({len(st.session_state.captcha_list)})")
    st.caption("Click panni manual-aa solve pannunga:")
    for item in st.session_state.captcha_list:
        st.markdown(f"- [{item}]({item})")
with c3:
    st.subheader(f"🔢 OTP Needed ({len(st.session_state.otp_list)})")
    st.caption("Code enter panna link open pannunga:")
    for item in st.session_state.otp_list:
        st.markdown(f"- [{item}]({item})")
with c4:
    st.subheader(f"❌ Failed ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
