import streamlit as st
import time
import gc
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber", layout="wide")
st.title("Universal Auto-Subscriber (Crash-Proof)")

@st.cache_resource
def install_playwright_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.caption(f"Browser check: {e}")

install_playwright_browsers()

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
        captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], iframe[src*='turnstile' i], div[class*='captcha' i], text=/robot|captcha|access denied|cloudflare|just a moment/i")
        return captcha.count() > 0
    except Exception:
        return False

def check_otp(page):
    try:
        otp = page.locator("input[name*='otp' i], input[id*='otp' i], input[placeholder*='code' i], input[name*='code' i], text=/verification code|enter otp|kód/i")
        return otp.count() > 0
    except Exception:
        return False

def smart_subscribe(page, user_email):
    try:
        # Check for email field in page or any popup
        email_field = page.locator("input[type='email'], input[name*='email' i], input[id*='email' i], input[placeholder*='mail' i]").first
        if email_field.count() > 0 and email_field.is_visible():
            name_field = page.locator("input[placeholder*='meno' i], input[name*='name' i], input[placeholder*='name' i], input[id*='name' i]").first
            if name_field.count() > 0 and name_field.is_visible():
                name_field.fill(fake.first_name())

            email_field.fill(user_email)
            time.sleep(0.5)

            checkbox = page.locator("input[type='checkbox']").first
            if checkbox.count() > 0 and checkbox.is_visible():
                try:
                    checkbox.check(force=True)
                except Exception:
                    pass

            submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('ZÍSKAŤ'), button:has-text('Zaregistrovať'), button:has-text('Subscribe'), button:has-text('Sign Up'), button:has-text('Prihlásiť'), button:has-text('Join')").first
            if submit_btn.count() > 0 and submit_btn.is_visible():
                submit_btn.click(timeout=3000)
                return True
            else:
                email_field.press("Enter")
                return True
    except Exception:
        pass
    return False

chromium_args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--blink-settings=imagesEnabled=false"
]

status_box = st.empty()
progress_bar = st.progress(0)

if st.session_state.is_running and urls:
    total_urls = len(urls)

    while st.session_state.current_index < total_urls and st.session_state.is_running:
        idx = st.session_state.current_index
        raw_url = urls[idx]
        url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

        status_box.info(f"Processing ({idx + 1}/{total_urls}): {url}")
        progress_bar.progress((idx + 1) / total_urls)

        # Isolated Playwright execution per site: Oru site crash aanaalum script crash aagathu
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=chromium_args)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    ignore_https_errors=True
                )
                page = context.new_page()
                page.route("**/*.{png,jpg,jpeg,svg,woff,woff2,gif,webp}", lambda route: route.abort())

                try:
                    page.goto(url, timeout=20000, wait_until="domcontentloaded")
                    time.sleep(2)

                    if check_captcha(page):
                        st.session_state.captcha_list.append(url)
                    else:
                        success = smart_subscribe(page, email)

                        if check_captcha(page):
                            st.session_state.captcha_list.append(url)
                        elif check_otp(page):
                            st.session_state.otp_list.append(url)
                        elif success:
                            st.session_state.success_list.append(url)
                        else:
                            st.session_state.failed_list.append((url, "Form / Newsletter box kaanala"))

                except Exception as site_err:
                    err_text = str(site_err)
                    if "Timeout" in err_text:
                        st.session_state.failed_list.append((url, "Site load aaga late aachu (Timeout)"))
                    else:
                        st.session_state.failed_list.append((url, f"Error: {err_text[:35]}"))

                finally:
                    context.close()
                    browser.close()

        except Exception as browser_crash:
            # Browser memory alavukku meeri crash aanaalum adutha site-ku jump aagidum
            st.session_state.failed_list.append((url, "Memory / Bot block (Skipped)"))

        gc.collect()
        st.session_state.current_index += 1

    if st.session_state.current_index >= total_urls:
        status_box.success("Ella domains-um process aaiduchu!")
        st.session_state.is_running = False
    elif not st.session_state.is_running:
        status_box.warning(f"Process paused! ({st.session_state.current_index}/{total_urls}) mudinjirukku. Continue panna 'Start / Continue' click pannunga.")

# 4 Columns Display
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.subheader(f"✅ Subscribed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"🧩 CAPTCHA / Access Denied ({len(st.session_state.captcha_list)})")
    st.caption("Direct-aa click panni solve pannunga:")
    for item in st.session_state.captcha_list:
        st.markdown(f"- [{item}]({item})")
with c3:
    st.subheader(f"🔢 OTP Needed ({len(st.session_state.otp_list)})")
    st.caption("Mail-la vantha OTP enter panna click pannunga:")
    for item in st.session_state.otp_list:
        st.markdown(f"- [{item}]({item})")
with c4:
    st.subheader(f"❌ Failed ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
