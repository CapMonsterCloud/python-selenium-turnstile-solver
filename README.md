# Cloudflare Turnstile Solver for Python Selenium with CapMonster Cloud

A runnable **Python Selenium** example that solves the **Cloudflare Turnstile** widget (the "Verify you are human" checkbox) using the official CapMonster Cloud Python SDK (`capmonstercloudclient`). Use it when Selenium automation gets stuck on Cloudflare Turnstile on forms you test or automate.

## What this example does

1. Starts Chrome through Selenium 4 and opens a page protected by a Turnstile widget.
2. Collects every parameter the widget was created with: `sitekey`, `action`, `cData` and the callback.
3. Sends a `TurnstileRequest` to CapMonster Cloud and receives a token.
4. Fills `cf-turnstile-response`, calls the page callback and can submit the form.

The default target is the public test form `tsmanaged.zlsupport.com`, so the first run works without any configuration except your API key.

## Requirements

- Python 3.9+
- Google Chrome (Selenium Manager downloads a matching chromedriver automatically)
- A CapMonster Cloud API key

## Quick start

```bash
git clone https://github.com/CapMonsterCloud/python-selenium-turnstile-solver.git
cd python-selenium-turnstile-solver
pip install -r requirements.txt

export CAPMONSTER_API_KEY=your_key        # Windows: set CAPMONSTER_API_KEY=your_key
python examples/solve_turnstile.py --headed

# your own page
python examples/solve_turnstile.py --url https://your-site.example/login --submit "button[type=submit]"
```

Run the tests (the browser test is skipped automatically if Chrome is missing):

```bash
pytest -q
```

## How it works

- **Hooking `turnstile.render()` before the page loads.** Many sites render Turnstile explicitly from JavaScript, so `action`, `cData` and the callback never appear in the HTML. The script registers `HOOK_RENDER_JS` through the Chrome DevTools command `Page.addScriptToEvaluateOnNewDocument`. The hook wraps `window.turnstile` as soon as Cloudflare's script defines it and records the options of every `render()` call.
- **Implicit widgets as a fallback.** For `<div class="cf-turnstile" data-sitekey=...>` the same values are read from `data-*` attributes. `merge_params()` prefers the hooked values because they are what the page really sent.
- **Passing `action` and `cData` matters.** If a site sets them, a token solved without them is rejected on the server side even though it looks valid.
- **Widget or full-page challenge.** `is_challenge_page()` detects the "Just a moment..." interstitial early and stops with a clear message instead of waiting for a widget that will never appear.

## Common errors

| Symptom | Cause and fix |
|---|---|
| `This version of ChromeDriver only supports Chrome version N` | An old chromedriver on `PATH` overrides Selenium Manager. Remove it or update Chrome and Selenium (`pip install -U selenium`). |
| `TimeoutException` while waiting for the widget | The widget is inside a modal or appears after a click. Open it first, or raise the wait time. |
| "This is a full-page Cloudflare Challenge" | The site shows Cloudflare's interstitial, not a widget. It needs the Cloudflare Challenge task type with your own proxy, not this example. |
| Token returned but the form is still rejected | `action`/`cData` were not captured, or the token was used after ~300 seconds. Make sure the hook ran (no `about:blank` reload) and submit right away. |
| `filled 0 input(s)` | The page has no `<form>`. Send the token to the site's API yourself. |
| `GetTaskError: [ERROR_KEY_DOES_NOT_EXIST]` / `[ERROR_ZERO_BALANCE]` | Check the API key or top up the balance. |

## Responsible use

Use this example only on websites you own or are authorized to test and automate, for example end-to-end tests of your own login forms. Follow the website's terms and applicable laws, and keep your API key out of source control.

## Links

- Python SDK: [CapMonster Cloud Python SDK](https://github.com/CapMonsterCloud/capmonster-python-captcha-solver)
- Cloudflare Turnstile solving with CapMonster Cloud: [capmonster.cloud/en/cloudflare-turnstile](https://capmonster.cloud/en/cloudflare-turnstile/?utm_source=github&utm_medium=repo-example&utm_campaign=python-selenium-turnstile)
