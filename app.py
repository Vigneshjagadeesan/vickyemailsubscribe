import streamlit as st
import time
import os
import subprocess
import re
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="100% Bulletproof Subscriber", layout="wide")
st.title("Universal Verified Account & Newsletter Engine")

@st.cache_resource
def install_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception:
        pass

install_browsers()

# Session State
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
    if st.button("▶️ Start Strict Verification Automation"):
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

def safe_show_step(page, msg, wait_sec=2):
    live_status.info(msg)
    try:
        if not page.is_closed():
            img_bytes = page.screenshot(timeout=4000)
            live_image.image(img_bytes, caption=msg, use_column_width=True)
    except Exception:
        pass
    time.sleep(wait_sec)

def safe_save_screenshot(page):
    try:
        if not page.is_closed():
            page.screenshot(path="current_screen.png", timeout=4000)
            return True
    except Exception:
        pass
    return False

def auto_accept_cookies(page):
    try:
        cookie_btns = page.locator("//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'prijat')]").first
        if cookie_btns.count() > 0 and cookie_btns.is_visible():
            cookie_btns.click(timeout=2000)
            time.sleep(1)
    except Exception:
        pass

def human_type(element, text):
    for char in text:
        element.type(char, delay=35)

def verify_confirmation(page):
    keywords = [
        "thank you", "thanks for subscribing", "thank you for joining", 
        "check your email", "confirmation link", "confirm your subscription", 
        "we have sent", "welcome to", "account created", "registra", "danke"
    ]
    try:
        body_text = page.inner_text("body", timeout=3000).lower()
        for kw in keywords:
            if kw in body_text:
                return True, kw
    except Exception:
        pass

    try:
        curr_url = page.url.lower()
        if any(w in curr_url for w in ["thank", "success", "confirmed", "welcome"]):
            return True, "URL Confirmation"
    except Exception:
        pass

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
                    ignore_https_errors=True,
                    viewport={"width": 1280, "height": 800}
                )
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page = context.new_page()

                # Memory save panna unnecessary images/media abort panrom
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["media", "font"] else route.continue_())

                # 1. Site Open
                safe_show_step(page, f"Step 1: Website open aagudhu -> {url}", wait_sec=2)
                page.goto(url, timeout=30000, wait_until="commit")
                time.sleep(3)

                # 2. Cookie Banner Click
                auto_accept_cookies(page)

                # 3. Popup Check
                popup_done = False
                try:
                    popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible, div[role='dialog']:visible").first
                    if popup.count() > 0:
                        p_email = popup.locator("input[type='email'], input[name*='email' i]").first
                        if p_email.count() > 0 and p_email.is_visible():
                            safe_show_step(page, "Popup vandhuduchu! Email fill pandrom...", wait_sec=1)
                            p_email.click()
                            human_type(p_email, email)
                            time.sleep(1)
                            
                            sub_btn = popup.locator("button[type='submit'], input[type='submit'], button:has-text('Subscribe'), button:has-text('Get'), button:has-text('Sign')").first
                            if sub_btn.count() > 0 and sub_btn.is_visible():
                                sub_btn.click(timeout=3000)
                            else:
                                p_email.press("Enter")
                            popup_done = True
                            time.sleep(4)
                except Exception:
                    pass

                # 4. In-page Newsletter / Register Form
                if not popup_done:
                    # Direct newsletter box thedurom
                    newsletter_box = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
                    if newsletter_box.count() > 0 and newsletter_box.is_visible():
                        safe_show_step(page, f"Newsletter box kandupidichom: {email}", wait_sec=1)
                        newsletter_box.click()
                        human_type(newsletter_box, email)
                        time.sleep(1)

                        # Submit button click
                        btn = page.locator("//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'subscribe') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'join') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign') or @type='submit']").first
                        if btn.count() > 0 and btn.is_visible():
                            btn.click(timeout=3000)
                        else:
                            newsletter_box.press("Enter")
                    else:
                        # Register page irundha mattum thedum
                        try:
                            reg_link = page.locator("//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'register') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign up')]").first
                            if reg_link.count() > 0 and reg_link.is_visible():
                                safe_show_step(page, "Register page open pandrom...", wait_sec=2)
                                reg_link.click(timeout=3000)
                                time.sleep(3)
                                auto_accept_cookies(page)
                                
                                reg_email = page.locator("input[type='email']").first
                                if reg_email.count() > 0 and reg_email.is_visible():
                                    reg_email.fill(email)
                                    # password
                                    for p_box in page.locator("input[type='password']").all():
                                        if p_box.is_visible():
                                            p_box.fill("VickySecure@2026#")
                                    page.keyboard.press("Enter")
                        except Exception:
                            pass

                time.sleep(5)

                # 5. Check CAPTCHA / OTP
                is_captcha = False
                is_otp = False
                try:
                    is_captcha = page.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha'], iframe[src*='turnstile'], text=/captcha|verify you are human|access denied/i").count() > 0
                    is_otp = page.locator("input[name*='otp' i], input[name*='code' i], text=/verification code|enter otp/i").count() > 0
                except Exception:
                    pass

                exact_url = page.url

                if is_captcha or is_otp:
                    safe_save_screenshot(page)
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = exact_url
                    st.session_state.pending_reason = "OTP Verification Kekkudhu" if is_otp else "CAPTCHA Security Protection Irukku"
                    context.close()
                    browser.close()
                    st.rerun()

                # 6. Verify Confirmation
                safe_show_step(page, "Confirmation message check pandrom...", wait_sec=2)
                confirmed, msg = verify_confirmation(page)

                if confirmed:
                    safe_show_step(page, f"✅ Confirmed: '{msg}' vandhuduchu! Mail trigger aaidum.", wait_sec=3)
                    st.session_state.success_list.append(url)
                else:
                    safe_save_screenshot(page)
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = exact_url
                    st.session_state.pending_reason = "Thank you / Success message varala. Direct link open panni verify pannunga."
                    context.close()
                    browser.close()
                    st.rerun()

                context.close()
                browser.close()

        except Exception as e:
            st.session_state.failed_list.append((url, str(e)[:40]))

        st.session_state.current_index += 1
        time.sleep(2)

    if st.session_state.current_index >= total_urls:
        live_status.success("Ellaa websites-um mudinjiduchu!")
        st.session_state.is_running = False

# Action Required Stop Area (Manual Solver)
if st.session_state.waiting_for_user:
    st.divider()
    st.subheader(f"⚠️ Action Required: Website Pause Aayirukku")
    st.error(f"Kaaranam: {st.session_state.pending_reason}")
    
    st.markdown(f"### 👉 [Inga Click Panni New Tab-la Open Pannunga: {st.session_state.pending_site}]({st.session_state.pending_site})")
    st.caption("Mela irukura link-a new tab-la open panni submit mudichittu keezha irukura button-a click pannunga:")
    
    if os.path.exists("current_screen.png"):
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
        if st.button("⏭️ Skip Intha Site"):
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
    st.subheader(f"✅ Confirmed Subscriptions ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed / Action Needed ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
