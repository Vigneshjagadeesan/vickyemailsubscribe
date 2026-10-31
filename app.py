import streamlit as st
import time
import os
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber (Interactive)", layout="wide")
st.title("Universal Auto-Subscriber (Interactive CAPTCHA & OTP Solver)")

@st.cache_resource
def install_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception:
        pass

install_browsers()

# Session State
if "browser" not in st.session_state:
    st.session_state.browser = None
if "page" not in st.session_state:
    st.session_state.page = None
if "playwright" not in st.session_state:
    st.session_state.playwright = None
if "pending_site" not in st.session_state:
    st.session_state.pending_site = None
if "pending_type" not in st.session_state:
    st.session_state.pending_type = None

email = st.text_input("Enter Yahoo Email Address:", placeholder="example@yahoo.com")
single_domain = st.text_input("Target Website URL:", placeholder="https://bellalab.sk")

col_a, col_b = st.columns(2)

with col_a:
    if st.button("🚀 Fill & Process Website"):
        if not email or not single_domain:
            st.error("Email matrum Website URL rendum compulsory da!")
        else:
            if st.session_state.playwright is None:
                st.session_state.playwright = sync_playwright().start()
                st.session_state.browser = st.session_state.playwright.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
                )
                st.session_state.page = st.session_state.browser.new_page()

            page = st.session_state.page
            url = single_domain if single_domain.startswith("http") else f"https://{single_domain}"
            
            st.info(f"Opening and auto-filling details: {url}")
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(2)

            # Auto Fill Email & Fake Data
            email_field = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
            if email_field.count() > 0:
                name_field = page.locator("input[placeholder*='meno' i], input[name*='name' i]").first
                if name_field.count() > 0:
                    name_field.fill(fake.first_name())
                
                email_field.fill(email)

                # Consent Checkbox
                cb = page.locator("input[type='checkbox']").first
                if cb.count() > 0:
                    try:
                        cb.check(force=True)
                    except Exception:
                        pass

                # Submit Button
                btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Subscribe'), button:has-text('ZÍSKAŤ')").first
                if btn.count() > 0:
                    btn.click(timeout=3000)
                else:
                    email_field.press("Enter")
                
                time.sleep(3)

                # Screenshot capture
                page.screenshot(path="current_screen.png")

                captcha_check = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], text=/captcha|robot/i").count() > 0
                otp_check = page.locator("input[name*='otp' i], input[name*='code' i], text=/verification code|otp|kód/i").count() > 0

                if captcha_check or otp_check:
                    st.session_state.pending_site = url
                    st.session_state.pending_type = "OTP" if otp_check else "CAPTCHA"
                    st.warning(f"{st.session_state.pending_type} detected! Screen paathu keezha code enter pannunga.")
                else:
                    st.success("Subscribed successfully without OTP/CAPTCHA!")
            else:
                st.error("Email subscribe box kedaikala.")

# Interactive Solver Section
if st.session_state.pending_site and os.path.exists("current_screen.png"):
    st.divider()
    st.subheader(f"Verification Screen: {st.session_state.pending_site}")
    st.image("current_screen.png", caption="Current Website Screen")
    
    user_code = st.text_input(f"Enter {st.session_state.pending_type} code / text inga type pannunga:")
    
    if st.button("Submit Code to Website"):
        page = st.session_state.page
        code_input = page.locator("input[name*='otp' i], input[name*='code' i], input[id*='code' i], input[type='text']:visible").first
        if code_input.count() > 0:
            code_input.fill(user_code)
            code_input.press("Enter")
            time.sleep(3)
            page.screenshot(path="current_screen.png")
            st.success("Code successfully submitted!")
            st.session_state.pending_site = None
            st.rerun()
        else:
            st.error("Website-la OTP/CAPTCHA box kedaikala.")
