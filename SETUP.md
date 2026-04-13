# GitHub Actions Setup

This setup runs the scheduled mail job from Kevin's GitHub fork. It does not require a local machine to stay on.

## 1. Configure monitored domains

Edit `config/domains.txt` and add one Postmaster domain per line:

```text
example.com
example.org
```

The report fetches domain reputation and IP reputation from Google Postmaster for each domain in that file.

## 2. Configure DKIM selectors

Edit `config/dkim_selectors.txt` and add one DKIM selector per line:

```text
nce2048
nc2048
inb
```

## 3. Configure monitored IPs

Edit `config/ips.txt` and add one IP address per line.

Postmaster returns IP reputation data as part of each domain's traffic stats. The report highlights configured IPs when they appear in Postmaster's sampled IP reputation data.

## 4. Add GitHub Actions secrets

In Kevin's fork, open:

**Settings -> Secrets and variables -> Actions -> New repository secret**

Add:

- `POSTMASTER_CLIENT_ID`
- `POSTMASTER_CLIENT_SECRET`
- `POSTMASTER_REFRESH_TOKEN`
- `POSTMASTER_SENDER_EMAIL`
- `POSTMASTER_SMTP_USERNAME`
- `POSTMASTER_SMTP_PASSWORD`
- `POSTMASTER_RECIPIENTS`
- `SMTP_HOST`
- `SMTP_PORT`

Do not commit these values into the repo.

## 5. Run manually once

Open **Actions -> Daily Postmaster Report -> Run workflow**.

Confirm:
- the workflow succeeds
- the email arrives
- the listed domains are correct
- the IP reputation data appears in the report

## 6. Schedule

The workflow runs daily at 9:00 AM Asia/Kolkata:

```yaml
cron: '30 3 * * *'
```

GitHub Actions cron uses UTC.
