# Google Postmaster Daily Monitor - Handoff for Kevin

Hi Kevin,

This repository is prepared as a starter project for a daily Google Postmaster monitoring system.

## What this project does
This project is designed to:
- fetch Google Postmaster Tools data for one or more domains
- monitor **domain reputation**
- monitor **IP reputation**
- check **SPF**, **DKIM**, and **DMARC** DNS records
- detect changes from the previous run
- send a daily HTML summary email every morning

## What is already included in this repo
The following has already been prepared:
- `monitor.py` - main monitoring script
- `.github/workflows/postmaster-report.yml` - daily GitHub Actions workflow
- `SETUP.md` - setup instructions for GitHub Actions
- `SETUP_GCP.md` - setup instructions for Google Cloud / Cloud Run
- `QUICK_DEPLOY.md` - quick deploy entrypoint including Open in Cloud Shell
- `Dockerfile`, `cloudbuild.yaml`, `deploy-cloud-run-job.sh` - Cloud Run deployment files

## Recommended deployment options
You have two usable deployment paths:

### Option 1 - GitHub Actions
Use this if you want the fastest way to get the report running.

Pros:
- simple setup
- daily schedule already included
- no infrastructure management

Best for:
- quick rollout
- email-only reporting

### Option 2 - Google Cloud Run + Cloud Scheduler
Use this if you want execution history and logs visible in Google Cloud Console.

Pros:
- visible in Google Cloud Console
- Cloud Run job execution history
- Cloud Logging support

Best for:
- production-style deployment
- teams that want monitoring visibility in GCP

## What you need to provide
Before the project can run, you need to provide the following values.

### Google Postmaster OAuth
These are required for accessing Google Postmaster Tools API:
- `POSTMASTER_CLIENT_ID`
- `POSTMASTER_CLIENT_SECRET`
- `POSTMASTER_REFRESH_TOKEN`

### Email delivery
These are required for sending the daily report email:
- `POSTMASTER_SENDER_EMAIL`
- `POSTMASTER_SMTP_USERNAME`
- `POSTMASTER_SMTP_PASSWORD`
- `POSTMASTER_RECIPIENTS`
- `SMTP_HOST`
- `SMTP_PORT`

### Monitoring configuration
These define what to monitor:
- `POSTMASTER_DOMAINS`
- `POSTMASTER_DKIM_SELECTORS`

## Example values
```text
POSTMASTER_DOMAINS=example.com,example.org
POSTMASTER_DKIM_SELECTORS=default,google,k1
POSTMASTER_RECIPIENTS=manager@company.com,deliverability@company.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
```

## Fastest path to get it running
If your goal is simply to start sending daily emails as soon as possible, use **GitHub Actions**.

### GitHub Actions setup steps
1. Open this repository.
2. Go to **Settings -> Secrets and variables -> Actions**.
3. Add all required secrets listed above.
4. Go to **Actions -> Daily Postmaster Report**.
5. Click **Run workflow**.
6. Confirm the email arrives correctly.

## Google Cloud path
If you want to view runs in Google Cloud Console:
1. Use the instructions in `SETUP_GCP.md`.
2. Deploy the job to Cloud Run.
3. Add environment variables or Secret Manager values.
4. Run it once manually.
5. Connect Cloud Scheduler for the daily run.

## Important notes
- DKIM checks depend on the correct selectors being provided.
- If a domain has no recent Postmaster data, some values may appear as `N/A`.
- The GitHub Actions version stores state in `state/state.json` to detect changes between runs.
- The Cloud Run path is included, but if you want persistent change tracking fully inside GCP, the state storage should later be moved to a persistent GCP store such as Cloud Storage or Firestore.

## Most likely causes of first-run issues
If the first run fails, the most common causes are:
- wrong Google account or missing Postmaster access
- invalid refresh token
- SMTP authentication failure
- wrong DKIM selector
- no recent Postmaster data for the selected domains

## Suggested next step
The quickest way to complete setup is:
1. decide between GitHub Actions or Cloud Run
2. provide the required credentials and domain details
3. run a manual test once
4. confirm the report email format and recipients

## Files to read first
- `SETUP.md`
- `SETUP_GCP.md`
- `QUICK_DEPLOY.md`

This repo is ready for you to complete deployment once the required credentials and configuration values are provided.
