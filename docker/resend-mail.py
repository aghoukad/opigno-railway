#!/usr/bin/python3
"""PHP sendmail transport for Resend HTTPS; no third-party Python dependencies."""

import base64
import json
import os
import sys
import time
import uuid
from email import policy
from email.headerregistry import Address
from email.parser import BytesParser
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


API_URL = "https://api.resend.com/emails"
MAX_BYTES = 40_000_000


class MailError(Exception):
    """A safe diagnostic that never includes message content or credentials."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def configuration(env):
    key = env.get("RESEND_API_KEY", "").strip()
    sender = env.get("RESEND_FROM_EMAIL", "").strip()
    name = env.get("RESEND_FROM_NAME", "").strip() or env.get("OPIGNO_SITE_NAME", "Opigno LMS")
    if not key or not sender:
        raise MailError("Set RESEND_API_KEY and RESEND_FROM_EMAIL in the Opigno service variables.")
    if any(c in key + sender + name for c in "\r\n\x00"):
        raise MailError("Invalid Resend configuration.")
    try:
        address = Address(display_name=name, addr_spec=sender)
        if not address.username or not address.domain:
            raise ValueError()
    except ValueError:
        raise MailError("RESEND_FROM_EMAIL must be one email address on a Resend-verified domain.") from None
    return key, str(address)


def addresses(message, header):
    result = []
    for value in message.get_all(header, []):
        if value.defects:
            raise MailError("Invalid email address header.")
        for address in value.addresses:
            if not address.username or not address.domain:
                raise MailError("Invalid email address header.")
            result.append(str(address))
    return result


def payload_from_mime(raw, sender):
    if len(raw) > MAX_BYTES:
        raise MailError("Email exceeds Resend's 40 MB limit.")
    message = BytesParser(policy=policy.default).parsebytes(raw)
    if any(part.defects for part in message.walk()):
        raise MailError("Malformed MIME email.")
    payload = {"from": sender, "to": addresses(message, "To"), "subject": str(message.get("Subject", ""))}
    if not payload["to"]:
        raise MailError("Email has no To recipient.")
    for header, field in (("Cc", "cc"), ("Bcc", "bcc"), ("Reply-To", "reply_to")):
        if values := addresses(message, header):
            payload[field] = values
    if sum(len(payload.get(field, [])) for field in ("to", "cc", "bcc")) > 50:
        raise MailError("Email exceeds Resend's 50 recipient limit.")

    bodies = []
    for mime_type, field in (("plain", "text"), ("html", "html")):
        if (body := message.get_body(preferencelist=(mime_type,))) is not None:
            payload[field] = body.get_content()
            bodies.append(body)
    if not bodies:
        raise MailError("Email has no supported text or HTML body.")

    attachments = []

    def collect(part):
        # message/rfc822 is an attachment, even though the parser calls it multipart.
        if part.get_content_maintype() == "multipart":
            for child in part.iter_parts():
                collect(child)
            return
        if any(part is body for body in bodies):
            return
        if part.get_content_type() == "message/rfc822":
            content = b"\r\n".join(child.as_bytes(policy=policy.SMTP) for child in part.get_payload())
        else:
            content = part.get_payload(decode=True)
        if content is None:
            raise MailError("Unsupported email attachment encoding.")
        attachment = {
            "filename": part.get_filename() or f"attachment-{len(attachments) + 1}",
            "content": base64.b64encode(content).decode("ascii"),
            "content_type": part.get_content_type(),
        }
        if cid := part.get("Content-ID"):
            attachment["content_id"] = str(cid).strip().strip("<>")
        attachments.append(attachment)

    collect(message)
    if attachments:
        payload["attachments"] = attachments
    # Resend constructs MIME and delivery headers. Bcc must never be copied here.
    headers = {}
    for key, value in message.items():
        lower = key.lower()
        if lower in {"in-reply-to", "references", "list-unsubscribe", "list-unsubscribe-post"} or (
            lower.startswith("x-") and lower != "x-php-originating-script"
        ):
            headers[key] = str(value)
    if headers:
        payload["headers"] = headers
    if any(part.defects for part in message.walk()):
        raise MailError("Malformed MIME email.")
    return payload


def deliver(payload, key, opener=None, sleep=time.sleep):
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_BYTES:
        raise MailError("Email exceeds Resend's 40 MB limit after encoding.")
    # One key per invocation, reused for network retries, never a hash of content:
    # two intentional identical notifications must remain two separate emails.
    request = Request(API_URL, data=encoded, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "opigno-railway-resend/1.0",
        "Idempotency-Key": f"opigno/{uuid.uuid4()}",
    }, method="POST")
    opener = opener or build_opener(ProxyHandler({}), NoRedirect())
    for attempt in range(3):
        delay = 2 ** attempt
        try:
            with opener.open(request, timeout=15) as response:
                result = json.loads(response.read(65536))
                if not isinstance(result, dict) or not result.get("id"):
                    raise MailError("Resend returned an invalid acceptance response.")
                return
        except HTTPError as error:
            status = error.code
            retry_after = error.headers.get("Retry-After", "") if error.headers else ""
            error.close()
            if status not in {429, 500, 502, 503, 504} or attempt == 2:
                raise MailError(f"Resend rejected email (HTTP {status}); check its dashboard and service variables.") from None
            if retry_after.isdigit():
                delay = min(10, max(delay, int(retry_after)))
        except (URLError, TimeoutError, OSError):
            if attempt == 2:
                raise MailError("Resend connection failed after three attempts.") from None
        except (ValueError, UnicodeError):
            raise MailError("Resend returned an invalid acceptance response.") from None
        sleep(delay)


def main():
    try:
        key, sender = configuration(os.environ)
        if sys.argv[1:] == ["--check-config"]:
            return 0
        # PHP mail() supplies recipients as MIME headers through this fixed command.
        # Never interpret additional arguments as shell commands or configuration.
        args = sys.argv[1:]
        extra = args[2:]
        # Drupal supplies a Return-Path using -f; Resend owns the bounce address.
        valid_return_path = (len(extra) == 1 and extra[0].startswith("-f") and len(extra[0]) > 2) or (
            len(extra) == 2 and extra[0] == "-f" and not extra[1].startswith("-")
        )
        if args[:2] != ["-t", "-i"] or (extra and not valid_return_path):
            raise MailError("This transport supports only PHP mail() with -t -i.")
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        deliver(payload_from_mime(raw, sender), key)
        return 0
    except MailError as error:
        print(f"Opigno mail: {error}", file=sys.stderr)
        return 1
    except Exception:
        # Parser/runtime exceptions can contain private message data. Never dump them.
        print("Opigno mail: invalid message or unexpected transport failure.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
