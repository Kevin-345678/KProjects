# Google Postmaster Daily Email Monitor

This project fetches Google Postmaster Tools data, checks SPF/DKIM/DMARC health, compares with the previous run, and emails a daily summary.

The GitHub Actions setup runs from Kevin's fork and does not need a local machine to stay on.

## Update monitored entries

Edit TXT files instead of changing Python code:

- `config/domains.txt`: one Postmaster domain per line
- `config/dkim_selectors.txt`: one DKIM selector per line
- `config/ips.txt`: one monitored IP address per line

The IP reputation data is fetched from Google Postmaster for each configured domain and included in the email report. Configured IPs are highlighted when Postmaster includes them in the domain's sampled IP reputation data.

## Required GitHub secrets

Add these in **Settings -> Secrets and variables -> Actions**:

- `POSTMASTER_CLIENT_ID`
- `POSTMASTER_CLIENT_SECRET`
- `POSTMASTER_REFRESH_TOKEN`
- `POSTMASTER_SENDER_EMAIL`
- `POSTMASTER_SMTP_USERNAME`
- `POSTMASTER_SMTP_PASSWORD`
- `POSTMASTER_RECIPIENTS`
- `SMTP_HOST`
- `SMTP_PORT`

The workflow runs daily at 9:00 AM Asia/Kolkata by default and can also be run manually from the Actions tab.
