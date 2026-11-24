"""Browser-independent pieces of the Selenium Turnstile example (unit-tested)."""
from __future__ import annotations

import os

DEMO_URL = "http://tsmanaged.zlsupport.com"

# Injected before any page script runs (CDP Page.addScriptToEvaluateOnNewDocument).
# It wraps turnstile.render() to remember sitekey, action, cData and the callback,
# which are not visible in the DOM when the widget is rendered explicitly from JS.
HOOK_RENDER_JS = r"""
(() => {
  let real;
  Object.defineProperty(window, 'turnstile', {
    configurable: true,
    get() { return real; },
    set(value) {
      if (value && typeof value.render === 'function' && !value.__cmWrapped) {
        const original = value.render.bind(value);
        value.render = (el, opts = {}) => {
          window.__turnstileParams = {
            sitekey: opts.sitekey || null,
            action: opts.action || null,
            cData: opts.cData || null,
          };
          if (typeof opts.callback === 'function') window.__turnstileCallback = opts.callback;
          return original(el, opts);
        };
        value.__cmWrapped = true;
      }
      real = value;
    },
  });
})();
"""

# Reads parameters for implicitly rendered widgets: <div class="cf-turnstile" data-sitekey=...>
READ_ATTRS_JS = """
const el = document.querySelector('.cf-turnstile[data-sitekey], [data-sitekey]');
if (!el) return null;
return {
  sitekey: el.getAttribute('data-sitekey'),
  action: el.getAttribute('data-action'),
  cData: el.getAttribute('data-cdata'),
  callback: el.getAttribute('data-callback'),
};
"""

# Puts the token where the widget would and notifies the page.
INJECT_TOKEN_JS = """
const token = arguments[0], callbackName = arguments[1];
let inputs = document.querySelectorAll('input[name="cf-turnstile-response"]');
if (!inputs.length) {
  const form = document.querySelector('form');
  if (form) {
    const input = document.createElement('input');
    input.type = 'hidden'; input.name = 'cf-turnstile-response';
    form.appendChild(input);
    inputs = [input];
  }
}
inputs.forEach((i) => { i.value = token; });
let fn = window.__turnstileCallback;
if (!fn && callbackName && typeof window[callbackName] === 'function') fn = window[callbackName];
if (fn) fn(token);
return { inputs: inputs.length, callbackFired: Boolean(fn) };
"""


def merge_params(hooked: dict | None, attrs: dict | None) -> dict:
    """Combine values captured from turnstile.render() with data-* attributes.

    Hooked values win because they are what the page actually passed to Cloudflare.
    """
    hooked, attrs = hooked or {}, attrs or {}
    params = {
        "sitekey": hooked.get("sitekey") or attrs.get("sitekey"),
        "action": hooked.get("action") or attrs.get("action"),
        "cdata": hooked.get("cData") or attrs.get("cData"),
        "callback": attrs.get("callback"),
    }
    if not params["sitekey"]:
        raise ValueError("Turnstile sitekey not found: no render() call and no data-sitekey on the page")
    return params


def is_challenge_page(title: str, html: str) -> bool:
    """A full-page Cloudflare Challenge needs a different task type than the Turnstile widget."""
    return title.strip().lower() in {"just a moment...", "один момент…"} or "challenge-platform" in html and "cf-turnstile" not in html


def require_api_key(env: dict | None = None) -> str:
    env = os.environ if env is None else env
    key = (env.get("CAPMONSTER_API_KEY") or "").strip()
    if not key:
        raise SystemExit("CAPMONSTER_API_KEY is not set. Export it first, e.g. export CAPMONSTER_API_KEY=your_key")
    return key


def token_preview(token: str, size: int = 32) -> str:
    return token if len(token) <= size else f"{token[:size]}... ({len(token)} chars)"
