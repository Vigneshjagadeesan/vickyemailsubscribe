import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from faker import Faker
import pandas as pd
import subprocess
import sys

# Ensure Playwright browser binaries are present on Streamlit Cloud
@st.cache_resource
def install_playwright_browsers():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

install_playwright_browsers()

fake = Faker()

st.set_page_config(page_title="Bulk Inbound Subscriber", layout="wide")
st.title("Bulk Inbound Newsletter Automator (Cloud)")

col1, col2 = st.columns([1, 2])

with col1:
    target_email = st.text_input("Target Email Address", placeholder="user@example.com")
    domains_input = st.text_area(
        "Domain List (one per line)", 
        placeholder="example1.com\nexample2.com",
        height=250
    )
    start_btn = st.button("Start Bulk Subscription", type="primary")

async def process_domain(page, url, email):
    try:
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(4)

        # Captcha detection
        page_content = await page.content()
        if any(bot in page_content.lower() for bot in ["g-recaptcha", "cf-turnstile", "h-captcha", "recaptcha"]):
            return {"status": "Skipped (Captcha Present)", "link": url}

        # 1. Popup / Modal check
        modal_inputs = [
            "div[role='dialog'] input[type='email']",
            ".modal input[type='email']",
            "[class*='popup'] input[type='email']",
            "[class*='newsletter'] input[type='email']"
        ]
        for selector in modal_inputs:
            elem = await page.query_selector(selector)
            if elem and await elem.is_visible():
                await elem.fill(email)
                chk = await page.query_selector("div[role='dialog'] input[type='checkbox'], .modal input[type='checkbox']")
                if chk:
                    try: await chk.check()
                    except: pass
                btn = await page.query_selector("div[role='dialog'] button[type='submit'], .modal button[type='submit']")
                if btn:
                    await btn.click()
                    await asyncio.sleep(3)
                    return {"status": "Subscribed (Popup)", "link": url}

        # 2. Footer / Main Page Form
        page_inputs = [
            "footer input[type='email']",
            "form input[type='email']",
            "input[name*='email' i]",
            "input[placeholder*='email' i]",
            "input[id*='email' i]"
        ]
        for selector in page_inputs:
            elem = await page.query_selector(selector)
            if elem and await elem.is_visible():
                await elem.fill(email)
                chk = await page.query_selector("footer input[type='checkbox'], form input[type='checkbox']")
                if chk:
                    try: await chk.check()
                    except: pass
                btn = await page.query_selector("footer button, form button[type='submit'], button:has-text('Subscribe'), button:has-text('Sign Up')")
                if btn:
                    await btn.click()
                    await asyncio.sleep(3)
                    return {"status": "Subscribed (Form)", "link": url}

        return {"status": "Failed (Form Not Found)", "link": url}

    except Exception as e:
        err = str(e).split("\n")[0]
        if "ERR_NAME_NOT_RESOLVED" in err:
            return {"status": "Failed (Invalid Domain)", "link": url}
        if "Timeout" in err:
            return {"status": "Failed (Timeout)", "link": url}
        return {"status": f"Failed: {err[:25]}", "link": url}

with col2:
    st.subheader("Execution Status")
    status_bar = st.empty()
    progress_bar = st.progress(0)
    table_placeholder = st.empty()

    if start_btn:
        if not target_email or not domains_input.strip():
            st.error("Email and Domain list fill pannu da!")
        else:
            raw_domains = [d.strip() for d in domains_input.strip().split("\n") if d.strip()]
            results = []
            total = len(raw_domains)

            async def run_batch():
                async with async_playwright() as p:
                    # Cloud-la headless=True thaan work aagum
                    browser = await p.chromium.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                    )
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                        viewport={"width": 1280, "height": 720}
                    )
                    page = await context.new_page()

                    for index, domain in enumerate(raw_domains):
                        formatted_url = domain if domain.startswith("http") else f"https://{domain}"
                        status_bar.info(f"Processing ({index + 1}/{total}): **{formatted_url}**")
                        progress_bar.progress((index + 1) / total)

                        res = await process_domain(page, formatted_url, target_email)
                        results.append({
                            "Domain": formatted_url,
                            "Status": res["status"],
                            "Action Link": res["link"]
                        })
                        table_placeholder.dataframe(pd.DataFrame(results), use_container_width=True)

                    status_bar.success("Finished all domains!")
                    await browser.close()

            asyncio.run(run_batch())
