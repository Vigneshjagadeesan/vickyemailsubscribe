import streamlit as st
import time
import os
import subprocess
import gc
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Universal Newsletter Engine", layout="wide")
st.title("Universal Footer & Popup Newsletter Subscriber")

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
domains_input = st.text_area("Enter Domains / URLs (Oru line-ku oru domain):", placeholder="https://yulyoie.com\nhttps://bellalab.sk")

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

def verify_newsletter_success(page):
    keywords = [
        "grazie per l'iscrizione", "grazie", "thank you", "thanks for subscribing",
        "merci", "danke", "vielen dank", "dakujeme", "gracias",
        "check your email", "subscribed", "iscritto", "success"
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
        if "customer_posted=true" in curr_url or "contact_posted=true" in curr_url or "thank" in curr_url:
            return True, "URL parameter confirmed"
    except Exception:
        pass

    return False, None

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

                # Memory crash thadukka media elements abort panrom
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["media", "font"] else route.continue_())

                safe_show_step(page, f"Website open panrom: {url}")
                page.goto(url, timeout=30000, wait_until="commit")
                time.sleep(2)

                auto_accept_cookies(page)

                # Page full-aa check pannum
                input_field = page.locator("//input[@type='email' or contains(@name, 'email') or contains(@placeholder, 'email') or contains(@placeholder, 'indirizzo')]").first
                
                # Visible illa na footer-ku scroll pannum
                if input_field.count() == 0 or not input_field.is_visible():
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                    input_field = page.locator("//footer//input[@type='email' or contains(@name, 'email') or contains(@placeholder, 'email') or contains(@placeholder, 'indirizzo')]").first

                if input_field.count() > 0 and input_field.is_visible():
                    input_field.scroll_into_view_if_needed()
                    time.sleep(1)
                    input_field.click()
                    input_field.fill(email)
                    time.sleep(1)
                    safe_show_step(page, f"Email enter panniyachu: {email}")

                    btn = page.locator("//button[@type='submit' or contains(@class, 'newsletter') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'subscribe') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'iscriviti')]").first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click(timeout=2500)
                    else:
                        input_field.press("Enter")

                time.sleep(4)

                # CAPTCHA check
                is_captcha = False
                try:
                    is_captcha = page.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha'], iframe[src*='turnstile'], text=/captcha|access denied/i").count() > 0
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

                # Confirmation verify
                is_confirmed, match_msg = verify_newsletter_success(page)
                if is_confirmed:
                    safe_show_step(page, f"✅ Confirmed: {match_msg}!")
                    st.session_state.success_list.append(url)
                else:
                    safe_save_screenshot(page)
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = exact_url
                    st.session_state.pending_reason = "Thank you / Confirmation message varala"
                    context.close()
                    browser.close()
                    st.rerun()

                context.close()
                browser.close()

        except Exception as e:
            err_msg = str(e)
            if "ERR_NAME_NOT_RESOLVED" in err_msg:
                st.session_state.failed_list.append((url, "Domain illai / Invalid URL"))
            elif "closed" in err_msg:
                st.session_state.failed_list.append((url, "Browser crash / Heavy site"))
            else:
                st.session_state.failed_list.append((url, err_msg[:30]))

        gc.collect()
        st.session_state.current_index += 1
        time.sleep(1)

    if st.session_state.current_index >= total_urls:
        live_status.success("Ellaa websites-um process aaiduchu!")
        st.session_state.is_running = False

if st.session_state.waiting_for_user:
    st.divider()
    st.subheader(f"⚠️ Action Required for: {st.session_state.pending_site}")
    st.error(f"Kaaranam: {st.session_state.pending_reason}")
    st.markdown(f"👉 [Direct Link Open Panni Mudiyunga: {st.session_state.pending_site}]({st.session_state.pending_site})")

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
