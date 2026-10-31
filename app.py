import streamlit as st
import time
import os
import subprocess
import re
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Verified Subscriber", layout="wide")
st.title("Universal Verified Subscriber (Strict Success & Manual Assist)")

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
if "pending_reason" not in st.session_state:
    st.session_state.pending_reason = None

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Bulk Domains / URLs (Line by line):", placeholder="https://bellalab.sk\nhttps://cohopte.com")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start Step-by-Step Automation"):
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

# Live Status Screen Monitor
st.subheader("📺 Live Step-by-Step Monitor")
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

def check_success_message(page):
    """Page-la Thank you / Success confirmation varudha nu check pannum"""
    success_pattern = re.compile(
        r"thank\s*you|thanks|subscribed|success|welcome|confirmation|check\s*your\s*email|registra|úspešn|danke|merci", 
        re.I
    )
    try:
        page_text = page.inner_text("body", timeout=3000)
        if success_pattern.search(page_text):
            return True
    except Exception:
        pass
    
    current_url = page.url.lower()
    if any(k in current_url for k in ["thank", "success", "confirmed", "welcome", "account"]):
        return True

    return False

# Main Execution Loop
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

                # Step 1: Open Website
                show_step(page, f"Step 1: Website open panrom -> {url}", wait_sec=2)
                page.goto(url, timeout=30000, wait_until="commit")
                time.sleep(3)
                show_step(page, f"Step 2: Page load aaiduchu -> {url}", wait_sec=2)

                # Step 2: Popup check
                popup_found = False
                try:
                    popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible, div[role='dialog']:visible").first
                    if popup.count() > 0:
                        p_email = popup.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
                        if p_email.count() > 0 and p_email.is_visible():
                            show_step(page, "Step 3: Newsletter/Discount Popup-la email fill panrom...", wait_sec=2)
                            p_email.fill(email, timeout=2000)
                            p_btn = popup.locator("button[type='submit'], input[type='submit'], button:has-text('Subscribe'), button:has-text('ZÍSKAŤ')").first
                            if p_btn.count() > 0 and p_btn.is_visible():
                                p_btn.click(timeout=2000)
                            else:
                                p_email.press("Enter")
                            popup_found = True
                            time.sleep(4)
                except Exception:
                    pass

                # Step 3: Register / Account Icon click (Strictly avoid Login)
                if not popup_found:
                    try:
                        human_icon = page.locator("a[href*='account' i], a[href*='customer' i], svg[class*='user' i], i[class*='user' i]").first
                        if human_icon.count() > 0 and human_icon.is_visible():
                            show_step(page, "Step 3: Account/Register icon click panrom...", wait_sec=2)
                            human_icon.click(timeout=2000)
                            time.sleep(2)

                            reg_btn = page.locator("a:has-text('Register'), a:has-text('Sign up'), a:has-text('Create account'), a:has-text('Zaregistrovať')").first
                            if reg_btn.count() > 0 and reg_btn.is_visible():
                                reg_btn.click(timeout=2000)
                                time.sleep(2)
                    except Exception:
                        pass

                    # Step 4: Form details fill
                    show_step(page, "Step 4: Form details fill panrom...", wait_sec=2)
                    
                    # Name
                    try:
                        name_box = page.locator("input[placeholder*='name' i], input[name*='name' i], input[placeholder*='meno' i]").first
                        if name_box.count() > 0 and name_box.is_visible():
                            name_box.fill(fake.first_name(), timeout=1500)
                    except Exception:
                        pass

                    # Password
                    try:
                        pwd_boxes = page.locator("input[type='password']").all()
                        for pb in pwd_boxes:
                            if pb.is_visible():
                                pb.fill("Pass@2026#Secure", timeout=1000)
                    except Exception:
                        pass

                    # Checkbox
                    try:
                        cbs = page.locator("input[type='checkbox']").all()
                        for c in cbs:
                            c.check(force=True, timeout=1000)
                    except Exception:
                        pass

                    # Email & Submit
                    email_box = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
                    if email_box.count() > 0 and email_box.is_visible():
                        email_box.fill(email, timeout=2000)
                        time.sleep(1)
                        show_step(page, f"Email enter panniyachu ({email}), submit panrom...", wait_sec=2)
                        
                        btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Subscribe'), button:has-text('Sign up'), button:has-text('Register')").first
                        if btn.count() > 0 and btn.is_visible():
                            btn.click(timeout=2000)
                        else:
                            email_box.press("Enter")

                time.sleep(5)

                # Step 5: Check CAPTCHA / OTP / Access Denied
                is_captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], iframe[src*='turnstile' i], text=/robot|captcha|access denied/i").count() > 0
                is_otp = page.locator("input[name*='otp' i], input[name*='code' i], input[placeholder*='code' i], text=/verification code|enter otp|kód/i").count() > 0

                if is_captcha or is_otp:
                    page.screenshot(path="current_screen.png")
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = url
                    st.session_state.pending_reason = "OTP Verification Needed" if is_otp else "CAPTCHA / Security Check Detected"
                    context.close()
                    browser.close()
                    st.rerun()

                # Step 6: Strict Check for "Thank You" / Success confirmation
                show_step(page, "Step 5: Thank You / Confirmation message check panrom...", wait_sec=2)
                success_detected = check_success_message(page)

                if success_detected:
                    show_step(page, f"✅ Confirmed! Success message vandhuduchu: {url}", wait_sec=3)
                    st.session_state.success_list.append(url)
                else:
                    # Confirmation text varalana adutha site-ku automatic-aa pogaathu; user review-kku nikkum
                    page.screenshot(path="current_screen.png")
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = url
                    st.session_state.pending_reason = "Thank You / Confirmation message varala (Form submit aagalaya nu check pannunga)"
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
        live_status.success("Ellaa websites-um process aagi mudinjiduchu!")
        st.session_state.is_running = False

# Interactive Action Required Section
if st.session_state.waiting_for_user and os.path.exists("current_screen.png"):
    st.divider()
    st.subheader(f"⚠️ Action Required for: {st.session_state.pending_site}")
    st.error(f"Kaaranam: {st.session_state.pending_reason}")
    
    st.markdown(f"### 👉 [Click here to open and solve {st.session_state.pending_site}]({st.session_state.pending_site})")
    st.caption("Mela irukkura link-a open panni CAPTCHA / OTP / Form mudichittu keezha irukura green button-a click pannunga:")
    
    st.image("current_screen.png", caption="Current Website Status Screen")

    c_sub1, c_sub2 = st.columns([2, 5])
    with c_sub1:
        if st.button("✅ I have completed / Continue Next Site"):
            st.session_state.success_list.append(st.session_state.pending_site)
            st.session_state.current_index += 1
            st.session_state.waiting_for_user = False
            st.session_state.pending_site = None
            st.session_state.pending_reason = None
            st.session_state.is_running = True
            st.rerun()

    with c_sub2:
        if st.button("⏭️ Skip this Website"):
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
    st.subheader(f"✅ Verified & Subscribed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed / Skipped ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
