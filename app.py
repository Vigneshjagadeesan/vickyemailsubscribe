import streamlit as st
import time
import os
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Multi-Action Subscriber", layout="wide")
st.title("Universal Smart Subscriber (Popup + Register + Live Monitor)")

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
if "pending_type" not in st.session_state:
    st.session_state.pending_type = None

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Bulk Domains / URLs (Line by line):", placeholder="https://bellalab.sk\nhttps://cohopte.com")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start Smart Automation"):
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
        st.session_state.success_list = []
        st.session_state.failed_list = []
        if os.path.exists("current_screen.png"):
            try:
                os.remove("current_screen.png")
            except Exception:
                pass
        st.rerun()

st.divider()

# Live Monitor Interface
st.subheader("📺 Real-Time Action Monitor")
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

def fill_register_form(page, target_email):
    submitted = False
    
    # 1. Names
    try:
        fname = page.locator("input[name*='first' i], input[id*='first' i], input[placeholder*='first' i], input[placeholder*='meno' i]").first
        if fname.count() > 0 and fname.is_visible():
            fname.fill(fake.first_name(), timeout=1500)
    except Exception:
        pass

    try:
        lname = page.locator("input[name*='last' i], input[id*='last' i], input[placeholder*='last' i], input[placeholder*='priezvisko' i]").first
        if lname.count() > 0 and lname.is_visible():
            lname.fill(fake.last_name(), timeout=1500)
    except Exception:
        pass

    # 2. Email (Ignore login email if register specific email exists)
    try:
        reg_email = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
        if reg_email.count() > 0 and reg_email.is_visible():
            reg_email.fill(target_email, timeout=2000)
    except Exception:
        pass

    # 3. Password Auto-generation
    auto_pass = "VickyPass@2026#"
    try:
        pwd_inputs = page.locator("input[type='password']").all()
        for pwd in pwd_inputs:
            if pwd.is_visible():
                pwd.fill(auto_pass, timeout=1000)
    except Exception:
        pass

    # 4. Checkboxes (Terms, Policy, Subscribe to newsletter)
    try:
        boxes = page.locator("input[type='checkbox']").all()
        for b in boxes:
            try:
                b.check(force=True, timeout=1000)
            except Exception:
                pass
    except Exception:
        pass

    # 5. Submit Button (Register/Signup priority, strictly avoiding login)
    try:
        sub_btn = page.locator("button:has-text('Register'), button:has-text('Sign up'), button:has-text('Create account'), button:has-text('Vytvoriť'), button:has-text('Zaregistrovať'), input[value*='Register' i], button[type='submit'], input[type='submit']").first
        if sub_btn.count() > 0 and sub_btn.is_visible():
            sub_btn.click(timeout=2500)
            submitted = True
        else:
            page.keyboard.press("Enter")
            submitted = True
    except Exception:
        pass

    return submitted

# Main Process Execution Loop
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

                # 1. Open Website
                show_step(page, f"Step 1: Website open panrom -> {url}", wait_sec=1)
                page.goto(url, timeout=25000, wait_until="commit")
                time.sleep(3)
                show_step(page, f"Step 2: Page load aachu -> {url}", wait_sec=2)

                # 2. Priority 1: Check Popup / Modal
                popup_handled = False
                try:
                    popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible, div[role='dialog']:visible").first
                    if popup.count() > 0:
                        p_email = popup.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
                        if p_email.count() > 0 and p_email.is_visible():
                            show_step(page, "Step 3: Newsletter/Discount Popup kandupidichom! Fill panrom...", wait_sec=2)
                            p_email.fill(email, timeout=2000)
                            p_btn = popup.locator("button[type='submit'], input[type='submit'], button:has-text('Subscribe'), button:has-text('Get'), button:has-text('ZÍSKAŤ')").first
                            if p_btn.count() > 0 and p_btn.is_visible():
                                p_btn.click(timeout=2000)
                            else:
                                p_email.press("Enter")
                            popup_handled = True
                            time.sleep(3)
                            show_step(page, "Popup Form Submitted!", wait_sec=2)
                except Exception:
                    pass

                # 3. Priority 2: Human Icon -> Strict Sign Up / Register
                reg_opened = False
                if not popup_handled:
                    try:
                        human_icon = page.locator("a[href*='account' i], a[href*='customer' i], svg[class*='user' i], i[class*='user' i], [aria-label*='account' i]").first
                        if human_icon.count() > 0 and human_icon.is_visible():
                            show_step(page, "Step 3: Human / Account icon click panrom...", wait_sec=1)
                            human_icon.click(timeout=2000)
                            time.sleep(2)

                            # Strict Register / Sign Up search (Avoiding Login)
                            reg_link = page.locator("a:has-text('Register'), a:has-text('Sign up'), a:has-text('Create account'), a:has-text('Zaregistrovať'), a:has-text('Vytvoriť účet'), a[href*='register' i], a[href*='signup' i]").first
                            if reg_link.count() > 0 and reg_link.is_visible():
                                show_step(page, "Sign Up / Register page open panrom...", wait_sec=2)
                                reg_link.click(timeout=2500)
                                time.sleep(2.5)
                                reg_opened = True
                    except Exception:
                        pass

                    # 4. Fill Register or Page Form
                    if reg_opened:
                        show_step(page, "Step 4: Register details fill panrom (Name, Email, Strong Auto-Password)...", wait_sec=2)
                        fill_register_form(page, email)
                    else:
                        # Priority 3: Footer/Page Newsletter Form search
                        show_step(page, "Step 4: Page-la irukura subscribe box thedi fill panrom...", wait_sec=2)
                        gen_email = page.locator("input[type='email'], input[name*='email' i], input[placeholder*='mail' i]").first
                        if gen_email.count() > 0 and gen_email.is_visible():
                            gen_email.fill(email, timeout=2000)
                            time.sleep(0.5)
                            gen_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Subscribe'), button:has-text('Join'), button:has-text('Sign up')").first
                            if gen_btn.count() > 0 and gen_btn.is_visible():
                                gen_btn.click(timeout=2000)
                            else:
                                gen_email.press("Enter")

                time.sleep(4)

                # 5. Result Verification & Anti-Bot / OTP Check
                is_captcha = False
                is_otp = False
                try:
                    is_captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], iframe[src*='turnstile' i], text=/robot|captcha|access denied/i").count() > 0
                    is_otp = page.locator("input[name*='otp' i], input[name*='code' i], input[placeholder*='code' i], text=/verification code|enter otp|kód/i").count() > 0
                except Exception:
                    pass

                # CAPTCHA / OTP vandha script pause aagi ungalukku prompt kaatum
                if is_captcha or is_otp:
                    page.screenshot(path="current_screen.png")
                    st.session_state.waiting_for_user = True
                    st.session_state.pending_site = url
                    st.session_state.pending_type = "OTP" if is_otp else "CAPTCHA"
                    context.close()
                    browser.close()
                    st.rerun()

                # Final Success Step Monitor
                show_step(page, f"Step 5: Submitted! Final status screen kaatudhu: {url}", wait_sec=4)
                st.session_state.success_list.append(url)

                context.close()
                browser.close()

        except Exception as e:
            st.session_state.failed_list.append((url, str(e)[:30]))

        st.session_state.current_index += 1
        time.sleep(2)

    if st.session_state.current_index >= total_urls:
        live_status.success("Ellaa websites-um process aagi mudinjiduchu!")
        st.session_state.is_running = False

# Interactive Verification Section (Pause & Solve)
if st.session_state.waiting_for_user and os.path.exists("current_screen.png"):
    st.divider()
    st.subheader(f"⚠️ Action Required for: {st.session_state.pending_site}")
    st.info(f"Intha site-la **{st.session_state.pending_type}** vandhurukku. Direct link open panni illa keezha code enter panni solve pannunga:")
    
    st.markdown(f"👉 **Direct Site Link:** [{st.session_state.pending_site}]({st.session_state.pending_site})")
    st.image("current_screen.png", caption=f"Current {st.session_state.pending_type} Screen")

    user_code = st.text_input(f"Enter {st.session_state.pending_type} value (Code iruntha type pannunga):")

    c_sub1, c_sub2 = st.columns([2, 5])
    with c_sub1:
        if st.button("✅ I have solved / Continue Next Site"):
            st.session_state.success_list.append(st.session_state.pending_site)
            st.session_state.current_index += 1
            st.session_state.waiting_for_user = False
            st.session_state.pending_site = None
            st.session_state.is_running = True
            st.rerun()
    with c_sub2:
        if st.button("⏭️ Skip This Domain"):
            st.session_state.failed_list.append((st.session_state.pending_site, "Skipped by user"))
            st.session_state.current_index += 1
            st.session_state.waiting_for_user = False
            st.session_state.pending_site = None
            st.session_state.is_running = True
            st.rerun()

# Summary Dashboard
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader(f"✅ Subscribed / Registered ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"❌ Failed / Skipped ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
