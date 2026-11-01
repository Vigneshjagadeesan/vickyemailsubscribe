import streamlit as st
import time
import os
import subprocess
import re
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Direct Newsletter Subscriber", layout="wide")
st.title("Universal Footer Newsletter Subscriber (Strict Confirmation)")

@st.cache_resource
def install_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception:
        pass

install_browsers()

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
domains_input = st.text_area("Enter Bulk Domains / URLs (Oru line-ku oru domain):", placeholder="https://yulyoie.com\nhttps://bellalab.sk")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start Newsletter Subscription"):
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
        cookie_btns = page.locator("//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta')]").first
        if cookie_btns.count() > 0 and cookie_btns.is_visible():
            cookie_btns.click(timeout=2000)
            time.sleep(1)
    except Exception:
        pass

def verify_newsletter_success(page):
    # Multi-language success indicators (English, Italian, French, German, Slovak, Spanish)
    keywords = [
        "grazie per l'iscrizione", "grazie", "thank you", "thanks for subscribing",
        "merci", "danke", "vielen dank", "dakujeme", "gracias",
        "check your email", "subscribed", "iscritto"
    ]
    try:
        body_text = page.inner_text("body", timeout=4000).lower()
        for kw in keywords:
            if kw in body_text:
                return True, kw
    except Exception:
        pass

    try:
        curr_url = page.url.lower()
        if "customer_posted=true" in curr_url or "contact_posted=true" in curr_url or "thank" in curr_url:
            return True, "customer_posted URL confirmation"
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
                    viewport={"width": 1366, "height": 768}
                )
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page = context.new_page()

                # 1. Site Open
                safe_show_step(page, f"Step 1: Website open panrom -> {url}", wait_sec=2)
                page.goto(url, timeout=35000, wait_until="commit")
                time.sleep(3)

                # Cookie dismiss
                auto_accept_cookies(page)

                # 2. Direct-aa footer newsletter box thedrom
                safe_show_step(page, "Step 2: Footer newsletter box thedurom...", wait_sec=1)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

                # Multi-language footer email input target
                newsletter_input = page.locator("//footer//input[@type='email' or contains(@name, 'email') or contains(@placeholder, 'email') or contains(@placeholder, 'indirizzo') or contains(@placeholder, 'mail')] | //form[contains(@action, 'contact')]//input[@type='email'] | //input[@id='Email' or @name='contact[email]']").first
                
                # Footer scroll-la kedaikalana page full-aa search pannum
                if newsletter_input.count() == 0 or not newsletter_input.is_visible():
                    newsletter_input = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first

                form_submitted = False
                if newsletter_input.count() > 0 and newsletter_input.is_visible():
                    newsletter_input.scroll_into_view_if_needed()
                    time.sleep(1)
                    newsletter_input.click()
                    newsletter_input.fill(email)
                    time.sleep(1)
                    safe_show_step(page, f"Step 3: Email fill panniyaachu ({email})", wait_sec=2)

                    # Submit button or Enter
                    sub_btn = page.locator("//footer//button[@type='submit' or contains(@class, 'newsletter') or contains(@name, 'commit')] | //form[contains(@action, 'contact')]//button[@type='submit']").first
                    if sub_btn.count() > 0 and sub_btn.is_visible():
                        sub_btn.click(timeout=3000)
                        form_submitted = True
                    else:
                        newsletter_input.press("Enter")
                        form_submitted = True
                
                time.sleep(5)

                # 3. Security / CAPTCHA Check
                is_captcha = False
                try:
                    is_captcha = page.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha'], iframe[src*='turnstile'], text=/captcha|verify you are human|access denied/i").count() > 0
                except Exception:
                    pass

                exact_url = page.url

                if is_captcha:
                    safe_save_screenshot(page)
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = exact_url
                    st.session_state.pending_reason = "CAPTCHA / Security check vandhurukku"
                    context.close()
                    browser.close()
                    st.rerun()

                # 4. Strict Check for "Grazie per l'iscrizione" / "Thank you"
                safe_show_step(page, "Step 4: Confirmation message check pandrom...", wait_sec=2)
                is_confirmed, match_msg = verify_newsletter_success(page)

                if is_confirmed:
                    safe_show_step(page, f"✅ Confirmed: '{match_msg}' vandhuduchu! Next domain-ku porom.", wait_sec=3)
                    st.session_state.success_list.append(url)
                else:
                    safe_save_screenshot(page)
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = exact_url
                    st.session_state.pending_reason = "Confirmation text (Grazie / Thank you) varala. Direct link open panni verify pannunga."
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
        live_status.success("Ellaa websites-um process aagi mudinjiduchu!")
        st.session_state.is_running = False

# Action Required Stop Area
if st.session_state.waiting_for_user:
    st.divider()
    st.subheader(f"⚠️ Action Required for: {st.session_state.pending_site}")
    st.error(f"Kaaranam: {st.session_state.pending_reason}")
    
    st.markdown(f"### 👉 [Direct Link Open Panni Submit Pannunga: {st.session_state.pending_site}]({st.session_state.pending_site})")
    
    if os.path.exists("current_screen.png"):
        st.image("current_screen.png", caption="Current Status Screen")

    c_sub1, c_sub2 = st.columns([2, 5])
    with c_sub1:
        if st.button("✅ Naan Submit Pannitten / Next Site-ku Po"):
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
    st.subheader(f"✅ Confirmed Subscriptions ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed / Action Needed ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
