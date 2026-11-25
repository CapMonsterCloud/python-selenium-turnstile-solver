# Cloudflare Turnstile Solver for Python Selenium (CapMonster Cloud)

[![tests](https://github.com/CapMonsterCloud/python-selenium-turnstile-solver/actions/workflows/test.yml/badge.svg)](https://github.com/CapMonsterCloud/python-selenium-turnstile-solver/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Selenium 4.20+](https://img.shields.io/badge/Selenium-4.20%2B-43B02A?logo=selenium&logoColor=white)](https://www.selenium.dev/)

A runnable **Cloudflare Turnstile solver for Python Selenium**. It finds the Turnstile widget on a page, requests a token from the [CapMonster Cloud Cloudflare Turnstile solver](https://capmonster.cloud/en/cloudflare-turnstile/?utm_source=github&utm_medium=repo-example&utm_campaign=python-selenium-turnstile&utm_content=intro) through the official Python SDK (`capmonstercloudclient`), puts the token into the form and can submit it. Use it when your Selenium tests or automation get stuck on the "Verify you are human" checkbox of Cloudflare Turnstile on pages you own or are allowed to test.

## What this example does

1. Starts Chrome through Selenium 4 and opens a page protected by a Turnstile widget.
2. Collects every parameter the widget was created with: `sitekey`, `action`, `cData` and the callback.
3. Sends a `TurnstileRequest` to CapMonster Cloud and receives a token.
4. Fills `cf-turnstile-response`, calls the page callback and can submit the form.

The default target is the public test form `tsmanaged.zlsupport.com`, so the first run works without any configuration except your API key.

## Requirements

- Python 3.9+
- Google Chrome (Selenium Manager downloads a matching chromedriver automatically)
- A CapMonster Cloud API key (see [Get an API key](#get-an-api-key))

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

## Turnstile token basics

- The token goes into the hidden field `cf-turnstile-response` or into the widget callback.
- A token is valid for 300 seconds and can be validated only once, so request a new one for every submission and submit right away.
- The same `TurnstileTask` is used for Managed, Non-Interactive and Invisible widgets; you do not set the mode.

## Common errors

| Symptom | Cause and fix |
|---|---|
| `This version of ChromeDriver only supports Chrome version N` | An old chromedriver on `PATH` overrides Selenium Manager. Remove it or update Chrome and Selenium (`pip install -U selenium`). |
| `TimeoutException` while waiting for the widget | The widget is inside a modal or appears after a click. Open it first, or raise the wait time. |
| "This is a full-page Cloudflare Challenge" | The site shows Cloudflare's interstitial, not a widget. It needs the Cloudflare Challenge task type with your own proxy, not this example. |
| Token returned but the form is still rejected | `action`/`cData` were not captured, or the token was used after ~300 seconds. Make sure the hook ran (no `about:blank` reload) and submit right away. |
| `filled 0 input(s)` | The page has no `<form>`. Send the token to the site's API yourself. |
| `GetTaskError: [ERROR_KEY_DOES_NOT_EXIST]` / `[ERROR_ZERO_BALANCE]` | Check the API key or top up the balance. |

## Get an API key

This example needs a CapMonster Cloud account and API key. New users can get a $0.10 test balance to try the service; the steps are on the [Cloudflare Turnstile solver page](https://capmonster.cloud/en/cloudflare-turnstile/?utm_source=github&utm_medium=repo-example&utm_campaign=python-selenium-turnstile&utm_content=cta). There you will also find pricing, the API description and ready-made SDKs for Python, Node.js and C#.

## Responsible use

Use this example only on websites you own or are authorized to test and automate, for example end-to-end tests of your own login forms. Follow the website's terms and applicable laws, and keep your API key out of source control.

## Links

- Python SDK: [CapMonster Cloud Python SDK](https://github.com/CapMonsterCloud/capmonster-python-captcha-solver)
- Cloudflare Turnstile solving with CapMonster Cloud: [capmonster.cloud/en/cloudflare-turnstile](https://capmonster.cloud/en/cloudflare-turnstile/?utm_source=github&utm_medium=repo-example&utm_campaign=python-selenium-turnstile&utm_content=links)

Cloudflare and Turnstile are trademarks of Cloudflare, Inc. CapMonster Cloud is not affiliated with or endorsed by Cloudflare.
