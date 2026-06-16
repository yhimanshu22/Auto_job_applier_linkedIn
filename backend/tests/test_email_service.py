from unittest.mock import patch

from services.email import templates


def test_welcome_template_contains_brand():
    subject, text, html = templates.welcome_email(name="Alex")
    assert "LinkdApply" in subject
    assert "Alex" in text
    assert "dashboard" in html


def test_payment_receipt_template():
    subject, text, html = templates.payment_receipt_email(
        name="Alex",
        plan="pro",
        billing_cycle="monthly",
        amount="3999.00",
        currency="INR",
        transaction_id="LA123",
        payment_provider="PayU",
        period_end="16 Jul 2026",
    )
    assert "receipt" in subject.lower()
    assert "LA123" in text
    assert "Pro" in html
    assert "3999.00" in html


def test_send_welcome_skips_without_smtp():
    from services.email.service import send_welcome

    with patch("services.email.transport.smtp_configured", return_value=False):
        assert send_welcome(email="user@example.com") is False


def test_notify_trial_started_calls_email_helpers():
    from services import billing_emails

    with patch("services.billing_emails.send_welcome", return_value=True) as welcome:
        with patch("services.billing_emails.send_trial_started", return_value=True) as trial:
            billing_emails.notify_onboarding_and_trial(
                email="user@example.com",
                expires_at="2026-06-17T12:00:00",
            )
    welcome.assert_called_once()
    trial.assert_called_once()
