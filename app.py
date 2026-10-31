import streamlit as st
import time
import os
import gc
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber", layout="wide")
st.title("Universal Bulk Subscriber (Crash-Proof Engine)")

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
if "pending_type" not in st.session_state:
    st.session_state.pending_type = None

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Bulk Domains / URLs (Line by line):", placeholder="https://bellalab.sk\nhttps://cohopte.com")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start / Continue Bulk Process"):
        if not email or not urls:
            st.error("Email matrum Bulk Domains list compulsory da!")
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
        st.session_state.success_list = []
        st.session_state.failed_list = []
        if os.path.exists("current_screen.png"):
            try:
                os.remove("current_screen.png")
            except Exception:
                pass
        st.rerun()

def fill_all_inputs(page, user_email):
    # 1. First Name
    try:
        first_name_input = page.locator("input[placeholder*='meno' i], input[name*='name' i], input[id*='name' i]").first
        if first_name_input.count() > 0 and first_name_input.is_visible():
            first_name_input.fill(fake.first_name(), timeout=2000)
    except Exception:
        pass

    # 2. Email
    try:
        email_input = page.locator("input[type='email'], input[name*='email' i], input[id*='email' i], input[placeholder*='mail' i]").first
        if email_input.count() > 0 and email_input.is_visible():
            email_input.fill(user_email, timeout=3000)
    except Exception:
        pass

    # 3. Password
    try:
        pass_input = page.locator("input[type='password']").first
        if pass_input.count() > 0 and pass_input.is_visible():
            pass_input.fill("AutoPass@2026", timeout=2000)
    except Exception:
        pass

    # 4. Checkboxes
    try:
        checkboxes = page.locator("input[type='checkbox']").all()
        for cb in checkboxes:
            try:
                cb.check(force=True, timeout=1000)
            except Exception:
                pass
    except Exception:
        pass

    # 5. Submit Button
    try:
        submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Register'), button:has-text('Sign up'), button:has-text('Subscribe'), button:has-text('ZÍSKAŤ')").first
        if submit_btn.count() > 0 and submit_btn.is_visible():
            submit_btn.click(timeout=3000)
            return True
        else:
            page.keyboard.press("Enter")
            return True
    except Exception:
        pass

    return False

browser_args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--no-zygote",
    "--disable-extensions"
]

status_box = st.empty()
progress_bar = st.progress(0)

# Automation Loop
if st.session_state.is_running and not st.session_state.waiting_for_user and urls:
    total_urls = len(urls)

    while st.session_state.current_index < total_urls and st.session_state.is_running:
        idx = st.session_state.current_index
        raw_url = urls[idx]
        url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

        status_box.info(f"Processing ({idx + 1}/{total_urls}): {url}")
        progress_bar.progress((idx + 1) / total_urls)

        # Ovvoru domain-kum individual Playwright context - crash aanaalum script stop aagadhu
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=browser_args)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    ignore_https_errors=True
                )
                page = context.new_page()

                # RAM crash thadukka images matrum heavy media-va block panrom
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

                try:
                    page.goto(url, timeout=20000, wait_until="domcontentloaded")
                    time.sleep(2)

                    # 1. Human / Profile / Account Icon click
                    try:
                        human_icon = page.locator("a[href*='account' i], a[href*='login' i], a[href*='registr' i], a[href*='prihlasenie' i], svg[class*='user' i], i[class*='user' i]").first
                        if human_icon.count() > 0 and human_icon.is_visible():
                            human_icon.click(timeout=2000)
                            time.sleep(1.5)
                            reg_tab = page.locator("a:has-text('Registr'), button:has-text('Registr'), a:has-text('Create account'), a:has-text('Sign up')").first
                            if reg_tab.count() > 0 and reg_tab.is_visible():
                                reg_tab.click(timeout=2000)
                                time.sleep(1)
                    except Exception:
                        pass

                    # 2. Popup modal check
                    try:
                        popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible, div[role='dialog']:visible").first
                        active_scope = popup if popup.count() > 0 else page
                    except Exception:
                        active_scope = page

                    # 3. Autofill inputs
                    fill_all_inputs(active_scope, email)
                    time.sleep(2)

                    # 4. CAPTCHA / OTP Check
                    is_captcha = False
                    is_otp = False
                    try:
                        is_captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], text=/robot|captcha|verification/i").count() > 0
                        is_otp = page.locator("input[name*='otp' i], input[name*='code' i], input[placeholder*='code' i], text=/verification code|enter otp|kód/i").count() > 0
                    except Exception:
                        pass

                    if is_captcha or is_otp:
                        page.screenshot(path="current_screen.png")
                        st.session_state.waiting_for_user = True
                        st.session_state.pending_site = url
                        st.session_state.pending_type = "OTP" if is_otp else "CAPTCHA"
                        context.close()
                        browser.close()
                        st.rerun()

                    st.session_state.success_list.append(url)

                except Exception as inner_err:
                    st.session_state.failed_list.append((url, str(inner_err)[:35]))
                finally:
                    try:
                        context.close()
                        browser.close()
                    except Exception:
                        pass

        except Exception as outer_err:
            # Browser crash aanaalum script nikaama adutha site-ku move aagidum
            st.session_state.failed_list.append((url, "Browser Timeout / RAM Crash"))

        gc.collect()
        st.session_state.current_index += 1

    if st.session_state.current_index >= total_urls:
        status_box.success("Ella domains-um process aaiduchu!")
        st.session_state.is_running = False

# Action Required / Pause Section
if st.session_state.waiting_for_user and os.path.exists("current_screen.png"):
    st.divider()
    st.subheader(f"⚠️ Action Required for: {st.session_state.pending_site}")
    st.image("current_screen.png", caption="Current Website Screenshot")
    
    user_code = st.text_input(f"Enter {st.session_state.pending_type} code / value:")
    
    col_s1, col_s2 = st.columns([2, 5])
    with col_s1:
        if st.button("Submit & Continue Bulk Process"):
            st.session_state.success_list.append(st.session_state.pending_site)
            st.session_state.current_index += 1
            st.session_state.waiting_for_user = False
            st.session_state.pending_site = None
            st.session_state.is_running = True
            st.rerun()

    with col_s2:
        if st.button("Skip This Domain"):
            st.session_state.failed_list.append((st.session_state.pending_site, "Skipped by user"))
            st.session_state.current_index += 1
            st.session_state.waiting_for_user = False
            st.session_state.pending_site = None
            st.session_state.is_running = True
            st.rerun()

# Results Section
c1, c2 = st.columns(2)
with c1:
    st.subheader(f"✅ Subscribed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed / Skipped ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
