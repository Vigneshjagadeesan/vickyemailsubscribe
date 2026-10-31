import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from faker import Faker
import urllib3

# InsecureRequestWarning hide panna
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

fake = Faker()

st.set_page_config(page_title="Universal Bulk Subscriber", layout="wide")
st.title("Universal Auto-Subscriber (Crash-Proof Engine)")

# State management
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "success_list" not in st.session_state:
    st.session_state.success_list = []
if "captcha_list" not in st.session_state:
    st.session_state.captcha_list = []
if "otp_list" not in st.session_state:
    st.session_state.otp_list = []
if "failed_list" not in st.session_state:
    st.session_state.failed_list = []

email = st.text_input("Enter unga Yahoo Email Address:", placeholder="example@yahoo.com")
domains_input = st.text_area("Enter Domains / URLs (Line by line):", placeholder="https://bellalab.sk")

urls = [u.strip() for u in domains_input.strip().splitlines() if u.strip()]

col_b1, col_b2, col_b3 = st.columns([1.5, 1.5, 4])
with col_b1:
    if st.button("▶️ Start / Continue"):
        if not email or not urls:
            st.error("Email matrum Domains compulsory da!")
        else:
            st.session_state.is_running = True

with col_b2:
    if st.button("⏹️ Stop / Pause"):
        st.session_state.is_running = False

with col_b3:
    if st.button("🔄 Reset All"):
        st.session_state.current_index = 0
        st.session_state.is_running = False
        st.session_state.success_list = []
        st.session_state.captcha_list = []
        st.session_state.otp_list = []
        st.session_state.failed_list = []
        st.rerun()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

def auto_subscribe_url(url, target_email):
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        res = session.get(url, timeout=12, verify=False)
        html = res.text.lower()

        # Cloudflare / Access Denied Check
        if res.status_code in [403, 503] or "cloudflare" in html or "access denied" in html or "cf-ray" in res.headers:
            return "CAPTCHA", "Cloudflare protection / Access Denied"

        soup = BeautifulSoup(res.text, "html.parser")

        # Forms-la subscribe/email box check pannum
        forms = soup.find_all("form")
        for form in forms:
            inputs = form.find_all(["input", "textarea"])
            has_email = False
            form_payload = {}

            for inp in inputs:
                inp_name = inp.get("name")
                if not inp_name:
                    continue
                inp_type = inp.get("type", "text").lower()
                inp_val = inp.get("value", "")

                if "email" in inp_name.lower() or inp_type == "email":
                    form_payload[inp_name] = target_email
                    has_email = True
                elif "name" in inp_name.lower() or "meno" in inp_name.lower():
                    form_payload[inp_name] = fake.first_name()
                elif "pass" in inp_name.lower():
                    form_payload[inp_name] = "SecurePass@2026"
                elif inp_type == "checkbox":
                    form_payload[inp_name] = inp_val if inp_val else "1"
                else:
                    form_payload[inp_name] = inp_val if inp_val else fake.word()

            if has_email:
                action = form.get("action")
                method = form.get("method", "post").lower()

                post_url = requests.compat.urljoin(url, action) if action else url

                if method == "post":
                    resp = session.post(post_url, data=form_payload, timeout=12, verify=False)
                else:
                    resp = session.get(post_url, params=form_payload, timeout=12, verify=False)

                resp_text = resp.text.lower()
                if "otp" in resp_text or "kód" in resp_text or "verification" in resp_text:
                    return "OTP", "OTP Required"
                return "SUCCESS", "Subscribed"

        # Direct email input search
        direct_email_input = soup.find("input", {"type": "email"}) or soup.find("input", {"name": re.compile(r"email", re.I)})
        if direct_email_input:
            return "SUCCESS", "Subscribed via direct field"

        return "FAILED", "No subscription form found"

    except requests.exceptions.Timeout:
        return "FAILED", "Timeout (Site slow)"
    except Exception as e:
        return "FAILED", str(e)[:35]

status_box = st.empty()
progress_bar = st.progress(0)

if st.session_state.is_running and urls:
    total_urls = len(urls)

    while st.session_state.current_index < total_urls and st.session_state.is_running:
        idx = st.session_state.current_index
        raw_url = urls[idx]
        url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"

        status_box.info(f"Processing ({idx + 1}/{total_urls}): {url}")
        progress_bar.progress((idx + 1) / total_urls)

        status, reason = auto_subscribe_url(url, email)

        if status == "SUCCESS":
            st.session_state.success_list.append(url)
        elif status == "CAPTCHA":
            st.session_state.captcha_list.append(url)
        elif status == "OTP":
            st.session_state.otp_list.append(url)
        else:
            st.session_state.failed_list.append((url, reason))

        st.session_state.current_index += 1

    if st.session_state.current_index >= total_urls:
        status_box.success("Ella websites-um process aaiduchu!")
        st.session_state.is_running = False
    elif not st.session_state.is_running:
        status_box.warning(f"Process paused! ({st.session_state.current_index}/{total_urls}) mudinjirukku.")

# Results Display
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.subheader(f"✅ Subscribed ({len(st.session_state.success_list)})")
    for item in st.session_state.success_list:
        st.write(f"- {item}")
with c2:
    st.subheader(f"🧩 CAPTCHA / Blocked ({len(st.session_state.captcha_list)})")
    st.caption("Direct-aa click panni solve pannunga:")
    for item in st.session_state.captcha_list:
        st.markdown(f"- [{item}]({item})")
with c3:
    st.subheader(f"🔢 OTP Needed ({len(st.session_state.otp_list)})")
    st.caption("Mail-la vantha OTP enter panna click pannunga:")
    for item in st.session_state.otp_list:
        st.markdown(f"- [{item}]({item})")
with c4:
    st.subheader(f"❌ Failed ({len(st.session_state.failed_list)})")
    for item, err in st.session_state.failed_list:
        st.write(f"- {item} ({err})")
