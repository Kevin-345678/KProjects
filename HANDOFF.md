# Handoff Checklist

This repo is ready as a starter implementation for a daily Google Postmaster report.

## What is already set up
- Python monitor script in `monitor.py`
- Daily GitHub Actions workflow in `.github/workflows/postmaster-report.yml`
- Google Cloud deployment files for Cloud Run in:
  - `Dockerfile`
  - `cloudbuild.yaml`
  - `deploy-cloud-run-job.sh`
  - `SETUP_GCP.md`
- Setup guide in `SETUP.md`

## What Kevin must provide
These values are required before the project can actually run:

### Google Postmaster OAuth
1. `POSTMASTER_CLIENT_ID`
2. `POSTMASTER_CLIENT_SECRET`
3. `POSTMASTER_REFRESH_TOKEN`

### Email sending
4. `POSTMASTER_SENDER_EMAIL`
5. `POSTMASTER_SMTP_USERNAME`
6. `POSTMASTER_SMTP_PASSWORD`
7. `POSTMASTER_RECIPIENTS`
8. `SMTP_HOST`
9. `SMTP_PORT`

### Monitoring config
10. `POSTMASTER_DOMAINS`
11. `POSTMASTER_DKIM_SELECTORS`

## Minimum values example
```text
POSTMASTER_DOMAINS=example.com,example.org
POSTMASTER_DKIM_SELECTORS=default,google,k1
POSTMASTER_RECIPIENTS=manager@company.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
```

## Fastest handover path
### Option A: GitHub Actions only
Best when they just want the job working fast.

Kevin should:
1. Open the repo
2. Add the required GitHub Actions secrets
3. Go to **Actions -> Daily Postmaster Report**
4. Click **Run workflow**
5. Confirm the email is received

### Option B: Google Cloud Console visibility
Best when they want to view runs in GCP.

Kevin should:
1. Deploy the container to Cloud Run Jobs using `deploy-cloud-run-job.sh`
2. Add env vars / Secret Manager values in Cloud Run
3. Execute the job once manually in Cloud Run
4. Add Cloud Scheduler for the daily run

## What is still needed to fully productionize it
- Real secrets and live domains
- Correct DKIM selectors for each domain
- A final test run
- Optional: persistent state storage for Cloud Run if they want change tracking outside GitHub

## If the first run fails
The most likely causes are:
- Wrong Google account / Postmaster access
- Bad refresh token
- SMTP auth failure
- Wrong DKIM selector
- No recent Postmaster data for a domain

## What to send Kevin
Send him this repo and ask for:
- the domain list
- DKIM selectors
- OAuth client ID
- OAuth client secret
- refresh token
- sender email
- SMTP username/password
- recipient email(s)

Once those are filled in, the project can be run and verified.
