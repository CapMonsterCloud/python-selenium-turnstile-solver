"""Solve a Cloudflare Turnstile widget in Selenium (Python) with the CapMonster Cloud SDK.

Usage:
    export CAPMONSTER_API_KEY=your_key
    python examples/solve_turnstile.py                       # demo form
    python examples/solve_turnstile.py --url https://your-site/login --submit "button[type=submit]"
"""
from __future__ import annotations

import argparse
import asyncio
import time

from capmonstercloudclient import CapMonsterClient, ClientOptions
from capmonstercloudclient.requests import TurnstileRequest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from turnstile_helpers import (
    DEMO_URL,
    HOOK_RENDER_JS,
    INJECT_TOKEN_JS,
    READ_ATTRS_JS,
    is_challenge_page,
    merge_params,
    require_api_key,
    token_preview,
)


def make_driver(headless: bool) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)  # Selenium Manager fetches a matching chromedriver
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": HOOK_RENDER_JS})
    return driver


def solve_token(api_key: str, url: str, params: dict, user_agent: str) -> str:
    client = CapMonsterClient(options=ClientOptions(api_key=api_key))
    request = TurnstileRequest(
        websiteURL=url,
        websiteKey=params["sitekey"],
        pageAction=params["action"],
        data=params["cdata"],
        userAgent=user_agent,
    )
    return asyncio.run(client.solve_captcha(request))["token"]


def run(url: str, submit_selector: str | None, headless: bool) -> str:
    api_key = require_api_key()
    driver = make_driver(headless)
    try:
        driver.get(url)
        if is_challenge_page(driver.title, driver.page_source):
            raise SystemExit("This is a full-page Cloudflare Challenge, not a Turnstile widget. See 'Common errors'.")

        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return window.__turnstileParams || null") or d.execute_script(READ_ATTRS_JS)
        )
        params = merge_params(driver.execute_script("return window.__turnstileParams || null"),
                              driver.execute_script(READ_ATTRS_JS))
        print(f"sitekey: {params['sitekey']}  action: {params['action']}  cData: {params['cdata']}")

        started = time.monotonic()
        token = solve_token(api_key, driver.current_url, params,
                            driver.execute_script("return navigator.userAgent"))
        print(f"solved in {time.monotonic() - started:.1f}s: {token_preview(token)}")

        result = driver.execute_script(INJECT_TOKEN_JS, token, params["callback"])
        print(f"filled {result['inputs']} input(s), callback fired: {result['callbackFired']}")

        if submit_selector:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, submit_selector))).click()
            print(f"submitted, now at {driver.current_url}")
        return token
    finally:
        driver.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=DEMO_URL, help="page with a Turnstile widget")
    parser.add_argument("--submit", default=None, help="CSS selector of the submit button")
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    args = parser.parse_args()
    run(args.url, args.submit, headless=not args.headed)


if __name__ == "__main__":
    main()
