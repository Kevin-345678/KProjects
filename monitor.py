import json
import os
import smtplib
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import dns.resolver
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/postmaster.readonly"]
STATE_PATH = Path("state/state.json")
TOKEN_URI = "https://oauth2.googleapis.com/token"


def env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value or ""


def parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def reputation_rank(value: str) -> int:
    order = {"BAD": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
    return order.get((value or "").upper(), -1)


def changed_direction(previous: str, latest: str) -> str:
    prev_rank = reputation_rank(previous)
    latest_rank = reputation_rank(latest)
    if prev_rank == -1 or latest_rank == -1:
        return "Unknown"
    if latest_rank > prev_rank:
        return "Improved"
    if latest_rank < prev_rank:
        return "Declined"
    return "No change"


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except json.JSONDecodeError:
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True))


def get_service():
    creds = Credentials(
        token=None,
        refresh_token=env("POSTMASTER_REFRESH_TOKEN", required=True),
        token_uri=TOKEN_URI,
        client_id=env("POSTMASTER_CLIENT_ID", required=True),
        client_secret=env("POSTMASTER_CLIENT_SECRET", required=True),
        scopes=SCOPES,
    )
    return build("gmailpostmastertools", "v1", credentials=creds, cache_discovery=False)


def fetch_domain_traffic(service, domain: str, days: int = 7) -> list[dict[str, Any]]:
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days)
    response = (
        service.domains()
        .trafficStats()
        .list(
            parent=f"domains/{domain}",
            startDate_day=start_date.day,
            startDate_month=start_date.month,
            startDate_year=start_date.year,
            endDate_day=end_date.day,
            endDate_month=end_date.month,
            endDate_year=end_date.year,
        )
        .execute()
    )
    stats = response.get("trafficStats", [])
    stats.sort(key=lambda item: (
        item.get("name", "").split("/trafficStats/")[-1]
    ))
    return stats


def latest_stat(stats: list[dict[str, Any]]) -> dict[str, Any] | None:
    return stats[-1] if stats else None


def extract_date(stat: dict[str, Any] | None) -> str:
    if not stat:
        return "N/A"
    name = stat.get("name", "")
    return name.split("/trafficStats/")[-1] or "N/A"


def extract_domain_reputation(stat: dict[str, Any] | None) -> str:
    value = (stat or {}).get("domainReputation", "N/A")
    return str(value).upper()


def extract_ip_reputation(stat: dict[str, Any] | None) -> str:
    items = (stat or {}).get("ipReputations", [])
    if not items:
        return "N/A"

    parts: list[str] = []
    for item in items:
        reputation = str(item.get("reputation", "UNKNOWN")).upper()
        sample_ips = item.get("sampleIps", [])
        volume = item.get("ipCount") or len(sample_ips)
        parts.append(f"{reputation}: {volume}")
    return "; ".join(parts)


def dns_txt_records(name: str) -> list[str]:
    answers = dns.resolver.resolve(name, "TXT")
    records: list[str] = []
    for answer in answers:
        if hasattr(answer, "strings"):
            joined = "".join(part.decode("utf-8") for part in answer.strings)
        else:
            joined = str(answer).strip('"')
        records.append(joined)
    return records


def check_spf(domain: str) -> tuple[str, str]:
    try:
        records = dns_txt_records(domain)
        for record in records:
            if record.lower().startswith("v=spf1"):
                return "OK", record
        return "Missing", "No SPF TXT record found"
    except Exception as exc:
        return "Error", str(exc)


def check_dmarc(domain: str) -> tuple[str, str]:
    try:
        records = dns_txt_records(f"_dmarc.{domain}")
        for record in records:
            if record.lower().startswith("v=dmarc1"):
                return "OK", record
        return "Missing", "No DMARC TXT record found"
    except Exception as exc:
        return "Error", str(exc)


def check_dkim(domain: str, selectors: list[str]) -> tuple[str, str]:
    tried: list[str] = []
    for selector in selectors:
        name = f"{selector}._domainkey.{domain}"
        tried.append(name)
        try:
            records = dns_txt_records(name)
            if records:
                return "OK", f"Selector {selector} found"
        except Exception:
            continue
    return "Missing", "No DKIM record found for selectors: " + ", ".join(tried)


def summarize_alerts(current: dict[str, Any], previous: dict[str, Any] | None) -> list[str]:
    alerts: list[str] = []
    prev = previous or {}

    latest_rep = current["domain_reputation"]
    prev_rep = prev.get("domain_reputation", "N/A")
    direction = changed_direction(prev_rep, latest_rep)
    if direction == "Declined":
        alerts.append(f"Domain reputation declined from {prev_rep} to {latest_rep}")
    elif direction == "Improved":
        alerts.append(f"Domain reputation improved from {prev_rep} to {latest_rep}")

    if latest_rep in {"LOW", "BAD"}:
        alerts.append(f"Domain reputation is {latest_rep}")

    for key, label in [("spf_status", "SPF"), ("dkim_status", "DKIM"), ("dmarc_status", "DMARC")]:
        current_status = current[key]
        previous_status = prev.get(key)
        if current_status != "OK":
            alerts.append(f"{label} status is {current_status}")
        elif previous_status and previous_status != current_status:
            alerts.append(f"{label} recovered from {previous_status} to OK")

    if prev.get("ip_reputation") and prev.get("ip_reputation") != current["ip_reputation"]:
        alerts.append("IP reputation mix changed")

    return alerts


def build_domain_snapshot(service, domain: str, selectors: list[str], previous_state: dict[str, Any]) -> dict[str, Any]:
    stats = fetch_domain_traffic(service, domain)
    current = latest_stat(stats)
    previous_stat = stats[-2] if len(stats) >= 2 else None

    spf_status, spf_detail = check_spf(domain)
    dkim_status, dkim_detail = check_dkim(domain, selectors)
    dmarc_status, dmarc_detail = check_dmarc(domain)

    snapshot = {
        "latest_date": extract_date(current),
        "previous_date": extract_date(previous_stat),
        "domain_reputation": extract_domain_reputation(current),
        "previous_domain_reputation": extract_domain_reputation(previous_stat),
        "ip_reputation": extract_ip_reputation(current),
        "previous_ip_reputation": extract_ip_reputation(previous_stat),
        "spf_status": spf_status,
        "spf_detail": spf_detail,
        "dkim_status": dkim_status,
        "dkim_detail": dkim_detail,
        "dmarc_status": dmarc_status,
        "dmarc_detail": dmarc_detail,
        "alerts": [],
    }
    snapshot["alerts"] = summarize_alerts(snapshot, previous_state.get(domain))
    return snapshot


def html_escape(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_email(report_date: str, snapshots: dict[str, dict[str, Any]]) -> str:
    rows = []
    detail_sections = []
    for domain, data in snapshots.items():
        alerts_html = "<br>".join(html_escape(alert) for alert in data["alerts"]) if data["alerts"] else "No alerts"
        rows.append(
            "<tr>"
            f"<td>{html_escape(domain)}</td>"
            f"<td>{html_escape(data['latest_date'])}</td>"
            f"<td>{html_escape(data['domain_reputation'])}</td>"
            f"<td>{html_escape(data['previous_domain_reputation'])}</td>"
            f"<td>{html_escape(data['ip_reputation'])}</td>"
            f"<td>{html_escape(data['spf_status'])}</td>"
            f"<td>{html_escape(data['dkim_status'])}</td>"
            f"<td>{html_escape(data['dmarc_status'])}</td>"
            f"<td>{alerts_html}</td>"
            "</tr>"
        )

        details = (
            f"<h3>{html_escape(domain)}</h3>"
            f"<ul>"
            f"<li><strong>Latest date:</strong> {html_escape(data['latest_date'])}</li>"
            f"<li><strong>Domain reputation:</strong> {html_escape(data['domain_reputation'])}</li>"
            f"<li><strong>Previous domain reputation:</strong> {html_escape(data['previous_domain_reputation'])}</li>"
            f"<li><strong>IP reputation:</strong> {html_escape(data['ip_reputation'])}</li>"
            f"<li><strong>Previous IP reputation:</strong> {html_escape(data['previous_ip_reputation'])}</li>"
            f"<li><strong>SPF:</strong> {html_escape(data['spf_status'])} - {html_escape(data['spf_detail'])}</li>"
            f"<li><strong>DKIM:</strong> {html_escape(data['dkim_status'])} - {html_escape(data['dkim_detail'])}</li>"
            f"<li><strong>DMARC:</strong> {html_escape(data['dmarc_status'])} - {html_escape(data['dmarc_detail'])}</li>"
            f"</ul>"
        )
        detail_sections.append(details)

    return f"""
    <html>
      <body style=\"font-family: Arial, sans-serif;\">
        <h2>Google Postmaster Daily Summary - {html_escape(report_date)}</h2>
        <p>This report includes domain reputation, IP reputation, and SPF/DKIM/DMARC checks for the configured domains.</p>
        <table border=\"1\" cellspacing=\"0\" cellpadding=\"8\" style=\"border-collapse: collapse; font-size: 14px;\">
          <thead>
            <tr>
              <th>Domain</th>
              <th>Latest Date</th>
              <th>Domain Rep</th>
              <th>Prev Domain Rep</th>
              <th>IP Rep</th>
              <th>SPF</th>
              <th>DKIM</th>
              <th>DMARC</th>
              <th>Alerts</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
        <hr>
        {''.join(detail_sections)}
      </body>
    </html>
    """


def send_email(html_body: str, subject: str) -> None:
    sender_email = env("POSTMASTER_SENDER_EMAIL", required=True)
    recipients = parse_list(env("POSTMASTER_RECIPIENTS", required=True))
    smtp_host = env("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(env("SMTP_PORT", "465"))
    smtp_username = env("POSTMASTER_SMTP_USERNAME", required=True)
    smtp_password = env("POSTMASTER_SMTP_PASSWORD", required=True)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = ", ".join(recipients)
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, recipients, message.as_string())


def main() -> None:
    domains = parse_list(env("POSTMASTER_DOMAINS", required=True))
    selectors = parse_list(env("POSTMASTER_DKIM_SELECTORS", "default,google"))

    service = get_service()
    previous_state = load_state()
    snapshots: dict[str, dict[str, Any]] = {}

    for domain in domains:
        snapshots[domain] = build_domain_snapshot(service, domain, selectors, previous_state)

    report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"Daily Postmaster Summary - {report_date}"
    html_body = render_email(report_date, snapshots)
    send_email(html_body, subject)

    next_state = deepcopy(previous_state)
    next_state.update(snapshots)
    save_state(next_state)


if __name__ == "__main__":
    main()
