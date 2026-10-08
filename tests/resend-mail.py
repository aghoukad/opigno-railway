"""Transport regression tests. All API calls are mocked; no email is sent."""

import base64
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from email.message import EmailMessage
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

path = Path(os.environ.get("RESEND_TRANSPORT_PATH", Path(__file__).parents[1] / "docker/resend-mail.py"))
spec = importlib.util.spec_from_loader("transport", SourceFileLoader("transport", str(path)))
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class TransportTest(unittest.TestCase):
    def fixture(self):
        message = EmailMessage()
        message["From"] = "Old sender <old@example.test>"
        message["To"] = '"Learner, One" <learner@example.test>, second@example.test'
        message["Cc"] = "copy@example.test"
        message["Bcc"] = "hidden@example.test"
        message["Reply-To"] = "support@example.test"
        message["Subject"] = "Votre certificat — مرحبا"
        message["X-Opigno-Test"] = "preserved"
        message["X-PHP-Originating-Script"] = "1000:private.php"
        message.set_content("Bonjour, voici votre certificat.\n")
        message.add_alternative('<p>Bonjour <img src="cid:logo" /></p>', subtype="html")
        message.get_payload()[1].add_related(b"PNG fixture", maintype="image", subtype="png", cid="<logo>")
        message.add_attachment(b"%PDF-1.4 fixture", maintype="application", subtype="pdf", filename="certificat.pdf")
        return message

    def test_mime_preserves_content_and_bcc_privacy(self):
        payload = transport.payload_from_mime(self.fixture().as_bytes(), "Opigno <notify@example.test>")
        self.assertEqual(payload["from"], "Opigno <notify@example.test>")
        self.assertEqual(len(payload["to"]), 2)
        self.assertEqual(payload["cc"], ["copy@example.test"])
        self.assertEqual(payload["bcc"], ["hidden@example.test"])
        self.assertEqual(payload["reply_to"], ["support@example.test"])
        self.assertEqual(payload["subject"], "Votre certificat — مرحبا")
        self.assertIn("Bonjour", payload["text"])
        self.assertIn('src="cid:logo"', payload["html"])
        self.assertEqual(payload["headers"], {"X-Opigno-Test": "preserved"})
        self.assertEqual(len(payload["attachments"]), 2)
        self.assertEqual(payload["attachments"][0]["content_id"], "logo")
        self.assertEqual(base64.b64decode(payload["attachments"][1]["content"]), b"%PDF-1.4 fixture")

    def test_plaintext_and_legacy_charset(self):
        payload = transport.payload_from_mime(
            b"To: test@example.test\nSubject: =?iso-8859-1?q?Certifi=E9?=\n"
            b"Content-Type: text/plain; charset=iso-8859-1\n\nCertifi\xe9\n", "sender@example.test")
        self.assertEqual(payload["subject"], "Certifié")
        self.assertEqual(payload["text"], "Certifié\n")
        self.assertNotIn("attachments", payload)

    def test_missing_or_invalid_configuration_is_rejected(self):
        for env in ({}, {"RESEND_API_KEY": "test"}, {"RESEND_FROM_EMAIL": "notify@example.test"},
                    {"RESEND_API_KEY": "test", "RESEND_FROM_EMAIL": "invalid"},
                    {"RESEND_API_KEY": "test", "RESEND_FROM_EMAIL": "a@example.test\nBcc: bad@example.test"}):
            with self.subTest(env=list(env)), self.assertRaises(transport.MailError):
                transport.configuration(env)
        self.assertEqual(transport.configuration({"RESEND_API_KEY": "test", "RESEND_FROM_EMAIL": "notify@example.test"}),
                         ("test", "Opigno LMS <notify@example.test>"))

    def test_bad_mime_or_recipient_is_rejected(self):
        for raw in (b"Subject: missing recipient\n\ntext", b"To: invalid\n\ntext",
                    b"To: test@example.test\nContent-Type: multipart/mixed; boundary=missing\n\ninvalid"):
            with self.subTest(raw=raw), self.assertRaises(transport.MailError):
                transport.payload_from_mime(raw, "sender@example.test")

    def test_api_retry_uses_one_idempotency_key(self):
        requests = []
        def open_request(request, timeout):
            self.assertEqual(timeout, 15)
            requests.append((request.get_header("Idempotency-key"), request.data))
            if len(requests) == 1:
                raise HTTPError(transport.API_URL, 429, "rate limited", {"Retry-After": "2"}, io.BytesIO())
            return io.BytesIO(b'{"id":"mock-accepted"}')
        opener = Mock()
        opener.open.side_effect = open_request
        sleep = Mock()
        transport.deliver({"text": "private message"}, "fake-test-key", opener=opener, sleep=sleep)
        self.assertEqual(requests[0], requests[1])
        sleep.assert_called_once_with(2)
        transport.deliver({"text": "private message"}, "fake-test-key", opener=opener, sleep=sleep)
        self.assertNotEqual(requests[1][0], requests[2][0])

    def test_api_errors_do_not_leak_private_content(self):
        for error in (HTTPError(transport.API_URL, 403, "fake-key/private-recipient", {}, io.BytesIO(b"secret")),
                      URLError("fake-key/private-recipient")):
            opener = Mock()
            opener.open.side_effect = error
            with self.assertRaises(transport.MailError) as context:
                transport.deliver({}, "fake-key", opener=opener, sleep=Mock())
            self.assertNotIn("fake-key", str(context.exception))
            self.assertNotIn("private-recipient", str(context.exception))
        self.assertEqual(opener.open.call_count, 3)

    def test_redirects_and_invalid_success_are_rejected(self):
        opener = Mock()
        opener.open.side_effect = HTTPError(transport.API_URL, 302, "redirect", {}, io.BytesIO())
        with self.assertRaises(transport.MailError):
            transport.deliver({}, "fake-test-key", opener=opener, sleep=Mock())
        self.assertEqual(opener.open.call_count, 1)
        self.assertIsNone(transport.NoRedirect().redirect_request(None, None, 302, None, None, "https://example.test"))
        opener.open.side_effect = lambda *args, **kwargs: io.BytesIO(b'{}')
        with self.assertRaises(transport.MailError):
            transport.deliver({}, "fake-test-key", opener=opener, sleep=Mock())

    def test_unconfigured_command_returns_failure_without_sendmail_error(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("RESEND_")}
        result = subprocess.run([sys.executable, str(path), "-t", "-i"], input=b"", capture_output=True, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"RESEND_API_KEY", result.stderr)
        self.assertNotIn(b"/usr/sbin/sendmail", result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)

    def test_php_return_path_argument_and_verified_sender(self):
        for extra in ([], ["-fold@example.test"], ["-f", "old@example.test"]):
            with patch.dict(os.environ, {"RESEND_API_KEY": "fake-test-key", "RESEND_FROM_EMAIL": "notify@example.test"}), \
                 patch.object(sys, "argv", [str(path), "-t", "-i"] + extra), \
                 patch.object(sys, "stdin", Mock(buffer=io.BytesIO(self.fixture().as_bytes()))), \
                 patch.object(transport, "deliver") as deliver:
                self.assertEqual(transport.main(), 0)
                self.assertIn("notify@example.test", deliver.call_args.args[0]["from"])
                self.assertEqual(deliver.call_args.args[1], "fake-test-key")

    @unittest.skipUnless(os.environ.get("OPIGNO_MAIL_FIXTURE"), "Run the Drupal fixture for the integration check")
    def test_actual_drupal_mime_mail_output(self):
        raw = Path(os.environ["OPIGNO_MAIL_FIXTURE"]).read_bytes()
        payload = transport.payload_from_mime(raw, "Opigno <notify@example.test>")
        self.assertEqual(payload["subject"], "Opigno Resend — certificat")
        self.assertIn("Resend integration", payload["html"])
        self.assertIn("Resend integration", payload["text"])
        self.assertEqual(payload["bcc"], ["hidden@example.test"])
        self.assertEqual(payload["reply_to"], ["support@example.test"])
        pdf = next(a for a in payload["attachments"] if a["filename"] == "resend-test.pdf")
        self.assertEqual(base64.b64decode(pdf["content"]), b"%PDF-1.4 integration fixture")


if __name__ == "__main__":
    unittest.main()
