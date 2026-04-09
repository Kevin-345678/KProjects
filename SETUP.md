# Setup Guide

## 1) What this project does
- Fetches Google Postmaster Tools data for your domains
- Checks domain reputation
- Checks IP reputation mix
- Checks SPF, DKIM, and DMARC DNS records
- Emails a daily HTML summary
- Detects changes using the previous run stored in `state/state.json`

## 2) Required Google OAuth values
You need these from Google Cloud Console:
- OAuth Client ID
- OAuth Client Secret
- Refresh Token

This project uses a refresh token because GitHub Actions cannot open a browser and complete interactive login.

## 3) Generate a refresh token once on your laptop
Create a file named `get_refresh_token.py` with this content:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/postmaster.readonly']
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)
print('refresh_token:', creds.refresh_token)
```

Install the required package:

```bash
pip install google-auth-oauthlib
```

Put your downloaded Google OAuth desktop-app `credentials.json` in the same folder and run:

```bash
python get_refresh_token.py
```

Copy the printed refresh token.

## 4) Add GitHub Actions secrets
In your repo go to:
**Settings -> Secrets and variables -> Actions**

Add these repository secrets:
- `POSTMASTER_CLIENT_ID`
- `POSTMASTER_CLIENT_SECRET`
- `POSTMASTER_REFRESH_TOKEN`
- `POSTMASTER_SENDER_EMAIL`
- `POSTMASTER_SMTP_USERNAME`
- `POSTMASTER_SMTP_PASSWORD`
- `POSTMASTER_RECIPIENTS`
- `POSTMASTER_DOMAINS`
- `POSTMASTER_DKIM_SELECTORS`
- `SMTP_HOST`
- `SMTP_PORT`

## 5) Example secret values
- `POSTMASTER_RECIPIENTS`: `manager@company.com,ops@company.com`
- `POSTMASTER_DOMAINS`: `example.com,example.org`
- `POSTMASTER_DKIM_SELECTORS`: `default,google,k1`
- `SMTP_HOST`: `smtp.gmail.com`
- `SMTP_PORT`: `465`

If you use Gmail SMTP, create a Gmail app password and use that as `POSTMASTER_SMTP_PASSWORD`.

## 6) Run it manually
Open the **Actions** tab in GitHub.
Open **Daily Postmaster Report**.
Click **Run workflow**.

## 7) Schedule
The workflow is currently set to run every day at `03:00 UTC`.
Update `.github/workflows/postmaster-report.yml` if you want a different time.

## 8) Notes
- DKIM is checked against the selectors in `POSTMASTER_DKIM_SELECTORS`.
- If a domain has no recent Postmaster data, the report may show `N/A`.
- The workflow commits updated state back to the repository after each run.
