import streamlit as st
import time
import os
import subprocess
import re
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Strict Register & Verified Subscriber", layout="wide")
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
    """Actual-aa confirmation text vandha mattum thaan True tharum"""
    success_keywords = [
        "thank you", "thanks for registering", "account created", 
        "check your email", "activation link", "confirm your email", 
        "welcome to", "success", "registration successful", "registra", "danke"
    ]
    try:
        body_text = page.inner_text("body", timeout=4000).lower()
        for kw in success_keywords:
            if kw in body_text:
                return True, kw
    except Exception:
        pass

    current_url = page.url.lower()
    if any(k in current_url for k in ["thank", "success", "registered", "account-created"]):
        return True, "URL confirmed"

    return False, None

# Main Loop
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

                # 1. Site Open
                show_step(page, f"Step 1: Website open pandrom -> {url}", wait_sec=2)
                page.goto(url, timeout=30000, wait_until="commit")
                time.sleep(4)

                # 2. Popup Check (Newsletter / Sign up popup mattum)
                try:
                    popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible, div[role='dialog']:visible").first
                    if popup.count() > 0:
                        p_email = popup.locator("input[type='email'], input[name*='email' i]").first
                        if p_email.count() > 0 and p_email.is_visible():
                            show_step(page, "Step 2: Popup kandupidichom, email fill pandrom...", wait_sec=2)
                            p_email.fill(email, timeout=2000)
                            p_btn = popup.locator("button[type='submit'], input[type='submit'], button:has-text('Sign'), button:has-text('Subscribe'), button:has-text('Get')").first
                            if p_btn.count() > 0 and p_btn.is_visible():
                                p_btn.click(timeout=2000)
                            else:
                                p_email.press("Enter")
                            time.sleep(4)
                except Exception:
                    pass

                # 3. Strictly find Register / Sign Up (Login-a complete-aa avoid pannum)
                reg_page_found = False
                show_step(page, "Step 3: Register / Create Account page thedurom (Login-a ignore pandrom)...", wait_sec=2)

                # First direct register links thedum
                reg_link = page.locator("a:has-text('Register'), a:has-text('Sign Up'), a:has-text('Create Account'), a:has-text('Join'), a[href*='register' i], a[href*='signup' i]").first
                if reg_link.count() > 0 and reg_link.is_visible():
                    reg_link.click(timeout=3000)
                    time.sleep(3)
                    reg_page_found = True
                else:
                    # Human icon kulla irundha click panni thedum
                    human_icon = page.locator("a[href*='account' i], svg[class*='user' i], i[class*='user' i], [aria-label*='account' i]").first
                    if human_icon.count() > 0 and human_icon.is_visible():
                        human_icon.click(timeout=2000)
                        time.sleep(2)
                        sub_reg = page.locator("a:has-text('Register'), a:has-text('Sign up'), a:has-text('Create'), a:has-text('Zaregistrovať')").first
                        if sub_reg.count() > 0 and sub_reg.is_visible():
                            sub_reg.click(timeout=3000)
                            time.sleep(3)
                            reg_page_found = True

                # 4. Fill Strict Registration Form
                show_step(page, "Step 4: Sign up form fill pandrom (Name, Email, Password)...", wait_sec=2)

                # First Name & Last Name
                try:
                    fn = page.locator("input[name*='first' i], input[placeholder*='first' i], input[id*='first' i], input[placeholder*='meno' i]").first
                    if fn.count() > 0 and fn.is_visible():
                        fn.fill(fake.first_name(), timeout=1500)
                except Exception:
                    pass

                try:
                    ln = page.locator("input[name*='last' i], input[placeholder*='last' i], input[id*='last' i]").first
                    if ln.count() > 0 and ln.is_visible():
                        ln.fill(fake.last_name(), timeout=1500)
                except Exception:
                    pass

                # Email
                try:
                    em_field = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
                    if em_field.count() > 0 and em_field.is_visible():
                        em_field.fill(email, timeout=2000)
                except Exception:
                    pass

                # Password Fields (Password & Confirm Password)
                try:
                    pwds = page.locator("input[type='password']").all()
                    for p_input in pwds:
                        if p_input.is_visible():
                            p_input.fill("VickySecure@2026!", timeout=1000)
                except Exception:
                    pass

                # Checkboxes (I agree, Terms, Newsletter)
                try:
                    cbs = page.locator("input[type='checkbox']").all()
                    for cb in cbs:
                        cb.check(force=True, timeout=1000)
                except Exception:
                    pass

                # Submit Click (Explicit Register/Sign up buttons)
                show_step(page, "Step 5: Form submit pandrom...", wait_sec=2)
                submit_clicked = False
                try:
                    btn = page.locator("button:has-text('Register'), button:has-text('Sign Up'), button:has-text('Create'), button:has-text('Vytvoriť'), button[type='submit'], input[type='submit']").first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click(timeout=3000)
                        submit_clicked = True
                    else:
                        page.keyboard.press("Enter")
                        submit_clicked = True
                except Exception:
                    pass

                time.sleep(6)  # Server response aaga nalla time vidurom

                # 5. Check for CAPTCHA / OTP / Access Block
                is_captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], iframe[src*='turnstile' i], text=/robot|captcha|access denied/i").count() > 0
                is_otp = page.locator("input[name*='otp' i], input[name*='code' i], input[placeholder*='code' i], text=/verification code|enter otp|kód/i").count() > 0

                if is_captcha or is_otp:
                    page.screenshot(path="current_screen.png")
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = url
                    st.session_state.pending_reason = "OTP Verification Kekkudhu" if is_otp else "CAPTCHA Security Protection Irukku"
                    context.close()
                    browser.close()
                    st.rerun()

                # 6. Strict Check for "Thank You" / Confirmation
                show_step(page, "Step 6: Confirmation message verify pandrom...", wait_sec=2)
                is_confirmed, match_msg = verify_confirmation(page)

                if is_confirmed:
                    show_step(page, f"✅ Confirmation vandhuduchu ({match_msg})! Adutha domain-ku porom.", wait_sec=3)
                    st.session_state.success_list.append(url)
                else:
                    # Confirmation text varalana adutha site-ku thaanaga pogaathu, stop aagi direct link kaatum
                    page.screenshot(path="current_screen.png")
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = url
                    st.session_state.pending_reason = "Thank you / Signup confirm aagala. Site direct-aa open panni check pannunga."
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
        live_status.success("Ellaa domains-um manual verification oda complete aaiduchu!")
        st.session_state.is_running = False

# Action Required Stop Area (Manual Solver)
if st.session_state.waiting_for_user and os.path.exists("current_screen.png"):
    st.divider()
    st.subheader(f"⚠️ Action Required for: {st.session_state.pending_site}")
    st.error(f"Reason: {st.session_state.pending_reason}")
    
    st.markdown(f"### 👉 [Inga Click Panni Site-a Open Pannunga: {st.session_state.pending_site}]({st.session_state.pending_site})")
    st.write("Mela irukkura link-a new tab-la open panni CAPTCHA / Signup mudichitu, vandha approm keezha irukura button-a click pannunga:")
    
    st.image("current_screen.png", caption="Current Site Status View")

    c_sub1, c_sub2 = st.columns([2, 5])
    with c_sub1:
        if st.button("✅ Naan Mudichitten / Continue Next Site"):
            st.session_state.success_list.append(st.session_state.pending_site)
            st.session_state.current_index += 1
            st.session_state.waiting_for_user = False
            st.session_state.pending_site = None
            st.session_state.pending_reason = None
            st.session_state.is_running = True
            st.rerun()

    with c_sub2:
        if st.button("⏭️ Skip Intha Website"):
            st.session_state.failed_list.append((st.session_state.pending_site, "Skipped by user"))
            st.session_state.current_index += 1
            st.session_state.waiting_for_user = False
            st.session_state.pending_site = None
            st.session_state.pending_reason = None
            st.session_state.is_running = True
            st.rerun()

# Summary Dashboard
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader(f"✅ Verified Signups ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed / Skipped ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
