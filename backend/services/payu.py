"""PayU India payment gateway helpers (hashing, pricing, verification)."""

from __future__ import annotations

import hashlib
import html
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Literal

import requests

Plan = Literal["starter", "pro", "agency"]
BillingCycle = Literal["monthly", "yearly"]

# INR amounts — keep in sync with frontend `PLANS` in pricing/page.tsx.
INR_PRICE_MAP: dict[BillingCycle, dict[Plan, int]] = {
    "monthly": {
        "starter": 1599,
        "pro": 3999,
        "agency": 11999,
    },
    "yearly": {
        "starter": 15588,
        "pro": 39588,
        "agency": 119988,
    },
}

PLAN_LABELS: dict[Plan, str] = {
    "starter": "LinkdApply Starter",
    "pro": "LinkdApply Pro",
    "agency": "LinkdApply Agency",
}


def _payu_key() -> str:
    return (os.getenv("PAYU_MERCHANT_KEY") or "").strip()


def _payu_salt() -> str:
    return (os.getenv("PAYU_MERCHANT_SALT") or "").strip()


def is_payu_configured() -> bool:
    return bool(_payu_key() and _payu_salt())


def payu_payment_url() -> str:
    if os.getenv("PAYU_ENV", "test").lower() == "production":
        return "https://secure.payu.in/_payment"
    return "https://test.payu.in/_payment"


def payu_postservice_url() -> str:
    if os.getenv("PAYU_ENV", "test").lower() == "production":
        return "https://info.payu.in/merchant/postservice?form=2"
    return "https://test.payu.in/merchant/postservice?form=2"


def format_amount(amount_inr: int | float) -> str:
    return f"{float(amount_inr):.2f}"


def get_inr_amount(plan: Plan, billing_cycle: BillingCycle) -> str:
    amount = INR_PRICE_MAP[billing_cycle][plan]
    return format_amount(amount)


def product_info(plan: Plan, billing_cycle: BillingCycle) -> str:
    cycle_label = "Annual" if billing_cycle == "yearly" else "Monthly"
    return f"{PLAN_LABELS[plan]} {cycle_label}"


def generate_txnid() -> str:
    # PayU: txnid must be unique, <= 25 chars, no special characters.
    return f"LA{int(time.time())}{secrets.token_hex(3)}"


def generate_request_hash(params: dict[str, str], salt: str) -> str:
    udf1 = params.get("udf1", "")
    udf2 = params.get("udf2", "")
    udf3 = params.get("udf3", "")
    udf4 = params.get("udf4", "")
    udf5 = params.get("udf5", "")
    hash_string = (
        f"{params['key']}|{params['txnid']}|{params['amount']}|{params['productinfo']}|"
        f"{params['firstname']}|{params['email']}|{udf1}|{udf2}|{udf3}|{udf4}|{udf5}"
        f"||||||{salt}"
    )
    return hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()


def verify_response_hash(params: dict[str, str], salt: str) -> bool:
    received = (params.get("hash") or "").lower()
    if not received:
        return False

    additional_charges = params.get("additionalCharges") or params.get("additional_charges")
    status = params.get("status", "")
    udf5 = params.get("udf5", "")
    udf4 = params.get("udf4", "")
    udf3 = params.get("udf3", "")
    udf2 = params.get("udf2", "")
    udf1 = params.get("udf1", "")

    if additional_charges:
        hash_string = (
            f"{additional_charges}|{salt}|{status}||||||{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|"
            f"{params.get('email', '')}|{params.get('firstname', '')}|"
            f"{params.get('productinfo', '')}|{params.get('amount', '')}|"
            f"{params.get('txnid', '')}|{params.get('key', '')}"
        )
    else:
        hash_string = (
            f"{salt}|{status}||||||{udf5}|{udf4}|{udf3}|{udf2}|{udf1}|"
            f"{params.get('email', '')}|{params.get('firstname', '')}|"
            f"{params.get('productinfo', '')}|{params.get('amount', '')}|"
            f"{params.get('txnid', '')}|{params.get('key', '')}"
        )

    calculated = hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()
    return calculated == received


def period_end_for_cycle(billing_cycle: BillingCycle) -> str:
    now = datetime.utcnow()
    if billing_cycle == "yearly":
        end = now + timedelta(days=365)
    else:
        end = now + timedelta(days=30)
    return end.isoformat()


def firstname_from_email(email: str) -> str:
    local = (email or "customer").split("@", 1)[0]
    cleaned = "".join(ch if ch.isalnum() or ch in " -_" else " " for ch in local).strip()
    return (cleaned or "Customer")[:60]


def build_payment_params(
    *,
    user_id: str,
    email: str,
    plan: Plan,
    billing_cycle: BillingCycle,
    success_url: str,
    failure_url: str,
    firstname: str | None = None,
    phone: str | None = None,
) -> dict[str, str]:
    key = _payu_key()
    salt = _payu_salt()
    if not key or not salt:
        raise ValueError("PayU merchant credentials are not configured")

    txnid = generate_txnid()
    amount = get_inr_amount(plan, billing_cycle)
    params: dict[str, str] = {
        "key": key,
        "txnid": txnid,
        "amount": amount,
        "productinfo": product_info(plan, billing_cycle),
        "firstname": firstname or firstname_from_email(email),
        "email": email,
        "phone": phone or os.getenv("PAYU_DEFAULT_PHONE", "8114245060"),
        "surl": success_url,
        "furl": failure_url,
        "udf1": user_id,
        "udf2": plan,
        "udf3": billing_cycle,
    }
    params["hash"] = generate_request_hash(params, salt)
    return params


def render_checkout_html(action: str, params: dict[str, str]) -> str:
    """PayU Hosted Checkout Step 1.3a — server-rendered auto-submit form."""
    fields = "\n".join(
        f'    <input type="hidden" name="{html.escape(k)}" value="{html.escape(v)}">'
        for k, v in params.items()
    )
    action_escaped = html.escape(action)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Redirecting to PayU…</title>
    <style>
      body {{ font-family: system-ui, sans-serif; display: grid; place-items: center; min-height: 100vh; margin: 0; background: #fafafa; color: #333; }}
      .box {{ text-align: center; padding: 2rem; }}
    </style>
  </head>
  <body onload="document.forms.payu.submit()">
    <div class="box">
      <p>Redirecting to secure PayU checkout…</p>
      <p><small>If you are not redirected, click Continue.</small></p>
    </div>
    <form name="payu" method="post" action="{action_escaped}">
{fields}
      <noscript><input type="submit" value="Continue to PayU"></noscript>
    </form>
  </body>
</html>"""


def verify_payment_with_payu(txnid: str) -> dict[str, Any] | None:
    """Optional server-side confirmation via PayU Verify Payment API."""
    key = _payu_key()
    salt = _payu_salt()
    if not key or not salt:
        return None

    command = "verify_payment"
    var1 = txnid
    api_hash = hashlib.sha512(
        f"{key}|{command}|{var1}|{salt}".encode("utf-8")
    ).hexdigest().lower()

    try:
        response = requests.post(
            payu_postservice_url(),
            data={
                "key": key,
                "command": command,
                "var1": var1,
                "hash": api_hash,
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") == 1:
            return payload.get("transaction_details", {}).get(txnid)
    except Exception as exc:
        print(f"PayU verify_payment failed for {txnid}: {exc}")
    return None
