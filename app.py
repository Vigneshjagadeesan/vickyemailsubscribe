import streamlit as st
import time
import random
import subprocess
from faker import Faker
from playwright.sync_api import sync_playwright

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber", layout="wide")
st.title("Universal Auto-Subscriber (Streamlit Cloud Ready)")

# Streamlit Cloud lo Chromium install cheyyadaniki auto-setup
@st.cache_resource
def install_playwright_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Playwright browser installation failed: {e}")

install_playwright_browsers()

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Domains / URLs (Line by line):", placeholder="https://bellalab.sk")

def check_captcha(page):
    captcha = page.locator("iframe[src*='recaptcha' i], iframe[src*='hcaptcha' i], iframe[src*='turnstile' i], div[class*='captcha' i], text=/robot|captcha|verification/i")
    return captcha.count() > 0

def check_otp(page):
    otp = page.locator("input[name*='otp' i], input[id*='otp' i], input[placeholder*='code' i], text=/verification code|enter otp|kód/i")
    return otp.count() > 0

def fill_all_inputs(scope, user_email):
    # 1. Name input
    name_input = scope.locator("input[placeholder*='meno' i], input[name*='name' i], input[placeholder*='name' i], input[id*='name' i]").first
    if name_input.count() > 0 and name_input.is_visible():
        name_input.fill(fake.first_name())

    # 2. Email input
    email_input = scope.locator("input[type='email'], input[placeholder*='e-mail' i], input[name*='email' i], input[id*='email' i]").first
    if email_input.count() > 0 and email_input.is_visible():
        email_input.fill(user_email)

    # 3. Password input
    pass_input = scope.locator("input[type='password']").first
    if pass_input.count() > 0 and pass_input.is_visible():
        pass_input.fill("Password@2026")

    # 4. Checkbox
    checkbox = scope.locator("input[type='checkbox']").first
    if checkbox.count() > 0 and checkbox.is_visible():
        try:
            checkbox.check(force=True)
        except Exception:
            pass

    # 5. Submit button click
    submit_btn = scope.locator("button[type='submit'], input[type='submit'], button:has-text('ZÍSKAŤ'), button:has-text('Zaregistrovať'), button:has-text('Subscribe'), button:has-text('Odoslať'), button:has-text('Prihlásiť')").first
    if submit_btn.count() > 0 and submit_btn.is_visible():
        submit_btn.click()
        return True
    return False

if st.button("Start Subscription Process"):
    if not email or not domains_input.strip():
        st.error("Email mariyu Domains compulsory ga ivvandi!")
    else:
        urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]
        success_list, captcha_list, otp_list, failed_list = [], [], [], []

        progress_bar = st.progress(0)
        status_text = st.empty()

        with sync_playwright() as p:
            # Streamlit Cloud Linux server kosam arguments tho launch
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page()

            for i, raw_url in enumerate(urls):
                url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"
                status_text.text(f"Processing ({i+1}/{len(urls)}): {url}")
                subscribed = False

                try:
                    page.goto(url, timeout=35000, wait_until="domcontentloaded")
                    time.sleep(3)

                    # CAPTCHA check
                    if check_captcha(page):
                        captcha_list.append(url)
                        continue

                    # Strategy 1: Popup detection
                    popup = page.locator("div[class*='modal']:visible, div[class*='popup']:visible, div[role='dialog']:visible").first
                    if popup.count() > 0:
                        if fill_all_inputs(popup, email):
                            subscribed = True
                            time.sleep(3)

                    # Strategy 2: User profile icon click
                    if not subscribed:
                        user_icon = page.locator("a[href*='account' i], a[href*='login' i], a[href*='prihlasenie' i], svg[class*='user' i], i[class*='user' i]").first
                        if user_icon.count() > 0 and user_icon.is_visible():
                            try:
                                user_icon.click()
                                time.sleep(2)
                                reg_tab = page.locator("a:has-text('Registr'), button:has-text('Registr'), a:has-text('Sign up')").first
                                if reg_tab.count() > 0:
                                    reg_tab.click()
                                    time.sleep(1)
                                if fill_all_inputs(page, email):
                                    subscribed = True
                                    time.sleep(3)
                            except Exception:
                                pass

                    # Strategy 3: Footer subscribe box
                    if not subscribed:
                        footer_scope = page.locator("footer, div[class*='footer' i]").first
                        scope_to_use = footer_scope if footer_scope.count() > 0 else page
                        if fill_all_inputs(scope_to_use, email):
                            subscribed = True
                            time.sleep(3)

                    # Results verification
                    if check_captcha(page):
                        captcha_list.append(url)
                    elif check_otp(page):
                        otp_list.append(url)
                    elif subscribed:
                        success_list.append(url)
                    else:
                        failed_list.append((url, "Form or Submit button dorakaledhu"))

                except Exception as e:
                    failed_list.append((url, f"Error: {str(e)[:45]}"))

                progress_bar.progress((i + 1) / len(urls))

            browser.close()

        status_text.success("Process Completed!")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.subheader(f"✅ Subscribed ({len(success_list)})")
            for item in success_list:
                st.write(f"- {item}")
        with c2:
            st.subheader(f"🧩 CAPTCHA ({len(captcha_list)})")
            st.caption("Click chesi solve cheyyandi:")
            for item in captcha_list:
                st.markdown(f"- [{item}]({item})")
        with c3:
            st.subheader(f"🔢 OTP Needed ({len(otp_list)})")
            st.caption("Code enter cheyyadaniki link open cheyyandi:")
            for item in otp_list:
                st.markdown(f"- [{item}]({item})")
        with c4:
            st.subheader(f"❌ Failed ({len(failed_list)})")
            for item, err in failed_list:
                st.write(f"- {item} ({err})")