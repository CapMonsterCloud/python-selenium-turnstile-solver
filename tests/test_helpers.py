import pytest

from turnstile_helpers import (
    INJECT_TOKEN_JS,
    is_challenge_page,
    merge_params,
    require_api_key,
    token_preview,
)


def test_hooked_render_values_win():
    hooked = {"sitekey": "0x4HOOK", "action": "login", "cData": "abc"}
    attrs = {"sitekey": "0x4ATTR", "action": None, "cData": None, "callback": "onDone"}
    assert merge_params(hooked, attrs) == {
        "sitekey": "0x4HOOK", "action": "login", "cdata": "abc", "callback": "onDone"
    }


def test_falls_back_to_data_attributes():
    attrs = {"sitekey": "0x4AAAAAAABUYP0XeMJF0xoy", "action": "contact", "cData": None, "callback": None}
    params = merge_params(None, attrs)
    assert params["sitekey"] == "0x4AAAAAAABUYP0XeMJF0xoy"
    assert params["action"] == "contact"


def test_missing_sitekey_is_explicit_error():
    with pytest.raises(ValueError, match="sitekey not found"):
        merge_params({}, None)


def test_detects_full_page_challenge():
    assert is_challenge_page("Just a moment...", "<html></html>")
    assert is_challenge_page("x", '<script src="/cdn-cgi/challenge-platform/h/b/orchestrate"></script>')
    assert not is_challenge_page("Login", '<div class="cf-turnstile" data-sitekey="0x4"></div>')


def test_api_key_and_preview():
    with pytest.raises(SystemExit, match="CAPMONSTER_API_KEY"):
        require_api_key({})
    assert require_api_key({"CAPMONSTER_API_KEY": "k"}) == "k"
    assert token_preview("t" * 100).endswith("(100 chars)")


def test_inject_script_in_headless_chrome():
    """Executes INJECT_TOKEN_JS in real Chrome against a local page; skipped if Chrome/driver are unavailable."""
    webdriver = pytest.importorskip("selenium.webdriver")
    from selenium.common.exceptions import WebDriverException

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Chrome not available: {exc.msg}")
    try:
        driver.get("data:text/html,<form><div class='cf-turnstile' data-sitekey='0x4' data-callback='done'></div></form>"
                   "<script>window.got=null;function done(t){window.got=t}</script>")
        result = driver.execute_script(INJECT_TOKEN_JS, "TOKEN123", "done")
        assert result == {"inputs": 1, "callbackFired": True}
        assert driver.execute_script("return window.got") == "TOKEN123"
        assert driver.execute_script(
            "return document.querySelector('input[name=cf-turnstile-response]').value") == "TOKEN123"
    finally:
        driver.quit()
