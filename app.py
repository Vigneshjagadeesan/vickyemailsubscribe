import streamlit as st
import time
import os
import subprocess
import gc
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Universal Newsletter Engine", layout="wide")
st.title("Universal Bulletproof Newsletter Subscriber")

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
domains_input = st.text_area("Enter Domains / URLs (Oru line-ku oru domain):", placeholder="https://kbombkratom.com\nhttps://yulyoie.com")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start Automation"):
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

# Stable Chromium flags for Streamlit Cloud (No crash, reliable renderer)
browser_args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-http2",
    "--ignore-certificate-errors",
    "--disable-blink-features=AutomationControlled"
]

def safe_show_step(page, msg, wait_sec=1):
    live_status.info(msg)
    try:
        if not page.is_closed():
            img_bytes = page.screenshot(timeout=3000)
            live_image.image(img_bytes, caption=msg, use_column_width=True)
    except Exception:
        pass
    time.sleep(wait_sec)

def safe_save_screenshot(page):
    try:
        if not page.is_closed():
            page.screenshot(path="current_screen.png", timeout=3000)
            return True
    except Exception:
        pass
    return False

def auto_accept_cookies(page):
    try:
        btn = page.locator("//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta')]").first
        if btn.count() > 0 and btn.is_visible():
            btn.click(timeout=1500)
            time.sleep(1)
    except Exception:
        pass

def handle_checkboxes(container):
    try:
        cbs = container.locator("input[type='checkbox']").all()
        for cb in cbs:
            try:
                if not cb.is_checked():
                    cb.check(force=True, timeout=1000)
            except Exception:
                try:
                    cb.click(force=True, timeout=1000)
                except Exception:
                    pass
    except Exception:
        pass

def verify_newsletter_success(page):
    keywords = [
        "grazie per l'iscrizione", "grazie", "thank you", "thanks for subscribing",
        "merci", "danke", "vielen dank", "dakujeme", "gracias",
        "check your email", "subscribed", "iscritto", "success", "welcome"
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
        if any(term in curr_url for term in ["customer_posted=true", "contact_posted=true", "thank", "success", "subscribed"]):
            return True, "URL confirmation"
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
                    viewport={"width": 1280, "height": 720}
                )
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page = context.new_page()

                # Block heavy media & fonts only, keep styles intact so layout does not crash
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["media", "font"] else route.continue_())

                safe_show_step(page, f"Step 1: Website open panrom: {url}", wait_sec=1)
                
                try:
                    page.goto(url, timeout=35000, wait_until="domcontentloaded")
                except Exception as e:
                    err_str = str(e)
                    if any(x in err_str for x in ["ERR_CONNECTION_CLOSED", "ERR_NAME_NOT_RESOLVED", "ERR_CONNECTION_REFUSED"]):
                        st.session_state.failed_list.append((url, "Site unavailable / Offline"))
                        context.close()
                        browser.close()
                        st.session_state.current_index += 1
                        continue

                time.sleep(3)
                auto_accept_cookies(page)

                # Step 2: Wait for Popup to trigger
                safe_show_step(page, "Step 2: Popup varudha nu wait pandrom...", wait_sec=2)
                time.sleep(3)

                submitted = False

                # Priority 1: Check Modal / Popup Newsletter
                try:
                    popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible, div[role='dialog']:visible, div[class*='newsletter-popup']:visible, div[id*='popup']:visible").first
                    if popup.count() > 0 and popup.is_visible():
                        p_email = popup.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
                        if p_email.count() > 0 and p_email.is_visible():
                            safe_show_step(page, "Popup vandhuduchu! Email fill pandrom...", wait_sec=1)
                            p_email.fill(email)
                            time.sleep(1)
                            handle_checkboxes(popup)
                            
                            p_btn = popup.locator("//button[@type='submit' or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'subscribe') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign')] | //input[@type='submit']").first
                            if p_btn.count() > 0 and p_btn.is_visible():
                                p_btn.click(timeout=2500)
                            else:
                                p_email.press("Enter")
                            submitted = True
                            time.sleep(4)
                except Exception:
                    pass

                # Priority 2: Page / Footer Newsletter if no popup appeared
                if not submitted:
                    safe_show_step(page, "Popup varala, Footer newsletter thedurom...", wait_sec=1)
                    page.keyboard.press("PageDown")
                    time.sleep(1)
                    page.keyboard.press("PageDown")
                    time.sleep(1)

                    input_field = page.locator("//input[@type='email' or contains(@name, 'email') or contains(@placeholder, 'email') or contains(@placeholder, 'indirizzo') or contains(@placeholder, 'mail')]").first
                    if input_field.count() > 0 and input_field.is_visible():
                        input_field.scroll_into_view_if_needed()
                        time.sleep(1)
                        input_field.click()
                        input_field.fill(email)
                        time.sleep(1)
                        safe_show_step(page, f"Email enter panniyachu: {email}")

                        handle_checkboxes(page)

                        btn = page.locator("//button[@type='submit' or contains(@class, 'newsletter') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'subscribe') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'iscriviti') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'join')]").first
                        if btn.count() > 0 and btn.is_visible():
                            btn.click(timeout=2500)
                        else:
                            input_field.press("Enter")
                        submitted = True

                time.sleep(5)

                # CAPTCHA check
                is_captcha = False
                try:
                    is_captcha = page.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha'], iframe[src*='turnstile'], text=/captcha|access denied|verify you are human/i").count() > 0
                except Exception:
                    pass

                exact_url = page.url

                if is_captcha:
                    safe_save_screenshot(page)
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = exact_url
                    st.session_state.pending_reason = "CAPTCHA Security Protection vandhurukku"
                    context.close()
                    browser.close()
                    st.rerun()

                # Confirmation Verify
                is_confirmed, match_msg = verify_newsletter_success(page)
                if is_confirmed:
                    safe_show_step(page, f"✅ Confirmed: {match_msg}! Next site-ku porom.", wait_sec=2)
                    st.session_state.success_list.append(url)
                else:
                    safe_save_screenshot(page)
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = exact_url
                    st.session_state.pending_reason = "Thank you / Success message varala. Check pannunga."
                    context.close()
                    browser.close()
                    st.rerun()

                context.close()
                browser.close()

        except Exception as e:
            err_msg = str(e)
            st.session_state.failed_list.append((url, err_msg[:35]))

        gc.collect()
        st.session_state.current_index += 1
        time.sleep(1)

    if st.session_state.current_index >= total_urls:
        live_status.success("Ellaa websites-um process aaiduchu!")
        st.session_state.is_running = False

# Action Required Stop Area
if st.session_state.waiting_for_user:
    st.divider()
    st.subheader(f"⚠️ Action Required for: {st.session_state.pending_site}")
    st.error(f"Kaaranam: {st.session_state.pending_reason}")
    st.markdown(f"### 👉 [Direct Link Open Panni Mudiyunga: {st.session_state.pending_site}]({st.session_state.pending_site})")

    if os.path.exists("current_screen.png"):
        st.image("current_screen.png", caption="Current Status Screen")

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
