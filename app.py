import streamlit as st
import time
import os
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Verified Subscriber", layout="wide")
st.title("Universal Verified Account Creator & Subscriber")

@st.cache_resource
def install_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception:
        pass

install_browsers()

# State Management
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
if "pending_reason" not in st.session_state:
    st.session_state.pending_reason = None

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Bulk Domains / URLs (Oru line-ku oru domain):", placeholder="https://bellalab.sk\nhttps://cohopte.com")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start Strict Registration"):
        if not email or not urls:
            st.error("Email matrum Domains list compulsory da!")
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
        st.session_state.pending_reason = None
        st.session_state.success_list = []
        st.session_state.failed_list = []
        if os.path.exists("current_screen.png"):
            try:
                os.remove("current_screen.png")
            except Exception:
                pass
        st.rerun()

st.divider()

# Live Monitor UI
st.subheader("📺 Real-Time Registration Monitor")
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

def verify_confirmation(page):
    success_keywords = [
        "thank you", "thanks for registering", "account created", 
        "check your email", "activation link", "confirm your email", 
        "welcome", "success", "registration successful", "registra", "danke"
    ]
    try:
        body_text = page.inner_text("body", timeout=3000).lower()
        for kw in success_keywords:
            if kw in body_text:
                return True, kw
    except Exception:
        pass

    try:
        current_url = page.url.lower()
        if any(k in current_url for k in ["thank", "success", "registered", "account-created"]):
            return True, "URL confirmed"
    except Exception:
        pass

    return False, None

# Main Process
if st.session_state.is_running and not st.session_state.waiting_for_user and urls:
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

                # Step 1: Open URL
                show_step(page, f"Step 1: Website open pandrom -> {url}", wait_sec=2)
                page.goto(url, timeout=30000, wait_until="commit")
                time.sleep(3)

                # Step 2: Popup check
                try:
                    popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible").first
                    if popup.count() > 0:
                        p_email = popup.locator("input[type='email']").first
                        if p_email.count() > 0 and p_email.is_visible():
                            show_step(page, "Popup-la email fill pandrom...", wait_sec=2)
                            p_email.fill(email, timeout=2000)
                            p_btn = popup.locator("button[type='submit'], input[type='submit']").first
                            if p_btn.count() > 0 and p_btn.is_visible():
                                p_btn.click(timeout=2000)
                            else:
                                p_email.press("Enter")
                            time.sleep(3)
                except Exception:
                    pass

                # Step 3: Register / Sign up Page Theduthal
                show_step(page, "Step 3: Register / Sign Up search pandrom...", wait_sec=2)
                try:
                    reg_link = page.locator("//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'register') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign up') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create')]").first
                    if reg_link.count() > 0 and reg_link.is_visible():
                        reg_link.click(timeout=3000)
                        time.sleep(3)
                    else:
                        human_icon = page.locator("a[href*='account'], svg[class*='user'], i[class*='user']").first
                        if human_icon.count() > 0 and human_icon.is_visible():
                            human_icon.click(timeout=2000)
                            time.sleep(2)
                            sub_reg = page.locator("//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'register') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign up')]").first
                            if sub_reg.count() > 0 and sub_reg.is_visible():
                                sub_reg.click(timeout=3000)
                                time.sleep(3)
                except Exception:
                    pass

                # Step 4: Safe Form Fill (No unexpected token "=" errors)
                show_step(page, "Step 4: Form details type pandrom...", wait_sec=2)
                try:
                    fn = page.locator("input[name*='first' i], input[id*='first' i]").first
                    if fn.count() > 0 and fn.is_visible():
                        fn.fill(fake.first_name(), timeout=1500)
                except Exception:
                    pass

                try:
                    ln = page.locator("input[name*='last' i], input[id*='last' i]").first
                    if ln.count() > 0 and ln.is_visible():
                        ln.fill(fake.last_name(), timeout=1500)
                except Exception:
                    pass

                try:
                    em_field = page.locator("input[type='email'], input[name*='email' i]").first
                    if em_field.count() > 0 and em_field.is_visible():
                        em_field.fill(email, timeout=2000)
                except Exception:
                    pass

                try:
                    pwds = page.locator("input[type='password']").all()
                    for p_input in pwds:
                        if p_input.is_visible():
                            p_input.fill("VickySecure@2026!", timeout=1000)
                except Exception:
                    pass

                try:
                    cbs = page.locator("input[type='checkbox']").all()
                    for cb in cbs:
                        cb.check(force=True, timeout=1000)
                except Exception:
                    pass

                # Step 5: Submit
                show_step(page, "Step 5: Form submit pandrom...", wait_sec=2)
                try:
                    sub_btn = page.locator("//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'register') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create') or @type='submit']").first
                    if sub_btn.count() > 0 and sub_btn.is_visible():
                        sub_btn.click(timeout=3000)
                    else:
                        page.keyboard.press("Enter")
                except Exception:
                    pass

                time.sleep(5)

                # Step 6: CAPTCHA / OTP / Access Denied Check
                is_captcha = False
                is_otp = False
                try:
                    is_captcha = page.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha'], iframe[src*='turnstile'], text=/captcha|access denied/i").count() > 0
                    is_otp = page.locator("input[name*='otp' i], input[name*='code' i], text=/verification code|enter otp/i").count() > 0
                except Exception:
                    pass

                if is_captcha or is_otp:
                    page.screenshot(path="current_screen.png")
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = url
                    st.session_state.pending_reason = "OTP Kekkudhu" if is_otp else "CAPTCHA Protection Vanthurukku"
                    context.close()
                    browser.close()
                    st.rerun()

                # Step 7: Confirmation verify
                is_confirmed, match_msg = verify_confirmation(page)
                if is_confirmed:
                    show_step(page, f"✅ Verified: {match_msg}! Next site porom.", wait_sec=3)
                    st.session_state.success_list.append(url)
                else:
                    # Confirmation varalana stop aagi direct link kaatum
                    page.screenshot(path="current_screen.png")
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = url
                    st.session_state.pending_reason = "Thank you / Confirmation message varala. Check pannunga."
                    context.close()
                    browser.close()
                    st.rerun()

                context.close()
                browser.close()

        except Exception as e:
            st.session_state.failed_list.append((url, str(e)[:35]))

        st.session_state.current_index += 1
        time.sleep(2)

    if st.session_state.current_index >= total_urls:
        live_status.success("Ellaa websites-um process aaiduchu!")
        st.session_state.is_running = False

# Manual Action Required Area
if st.session_state.waiting_for_user and os.path.exists("current_screen.png"):
    st.divider()
    st.subheader(f"⚠️ Action Required for: {st.session_state.pending_site}")
    st.error(f"Reason: {st.session_state.pending_reason}")
    
    st.markdown(f"### 👉 [Direct Link-a New Tab-la Open Panni Mudiyunga: {st.session_state.pending_site}]({st.session_state.pending_site})")
    st.caption("Link-a open panni manual-aa finish pannittu keezha irukura button-a click pannunga:")
    st.image("current_screen.png", caption="Current Website Status View")

    c_sub1, c_sub2 = st.columns([2, 5])
    with c_
