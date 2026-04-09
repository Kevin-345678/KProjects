# Google Cloud Console Setup

If you want to view job runs in Google Cloud Console, use **Cloud Run Jobs** plus **Cloud Scheduler**.

## Why this setup
- Cloud Run Jobs lets you view executions in the Cloud Run console.
- Cloud Run sends container logs to Cloud Logging automatically.
- Cloud Scheduler can trigger the job every morning.

## 1) Build and deploy the Cloud Run Job
Requirements:
- Google Cloud project
- gcloud CLI installed and authenticated
- Billing enabled for the project
- Cloud Run API, Cloud Build API, Artifact Registry API, and Cloud Scheduler API enabled

Run:

```bash
chmod +x deploy-cloud-run-job.sh
./deploy-cloud-run-job.sh YOUR_PROJECT_ID YOUR_REGION postmaster-monitor
```

Example:

```bash
./deploy-cloud-run-job.sh my-gcp-project asia-south1 postmaster-monitor
```

## 2) Add environment variables and secrets to the job
In Google Cloud Console:
1. Open **Cloud Run**
2. Open the **Jobs** tab
3. Click `postmaster-monitor`
4. Click **Edit and deploy new revision** or **Edit**
5. Add environment variables matching `.env.example`

Recommended values:
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

For better security, store sensitive values in **Secret Manager** and attach them as secrets to the job instead of plain environment variables.

## 3) Run it once manually
In Cloud Run console:
1. Go to **Cloud Run**
2. Open the job
3. Click **Execute**

This lets you confirm the email works.

## 4) View runs in Google Cloud Console
You can view:
- Job executions in **Cloud Run -> Jobs -> postmaster-monitor**
- Logs in the **LOGS** tab for the job or a specific execution
- Full logs in **Cloud Logging -> Logs Explorer**

## 5) Create a scheduler job
Use Cloud Scheduler to trigger it every morning.

### Simplest method from the console
1. Open **Cloud Scheduler**
2. Click **Create job**
3. Name: `postmaster-monitor-daily`
4. Schedule: for example `0 9 * * *`
5. Choose your timezone
6. Target type: **HTTP**

Then configure the target to invoke the Cloud Run Job execution endpoint through an authenticated call, or use a lightweight Cloud Run service wrapper if you prefer an HTTP endpoint.

## 6) Easier alternative if you want a direct HTTP scheduler target
If you do not want to call the Cloud Run Jobs execution API, you can instead deploy this as a **Cloud Run service** and have Cloud Scheduler hit its URL daily.
That setup is easier to schedule, but Cloud Run Jobs is cleaner for batch work and gives you execution history directly in the Cloud Run jobs UI.

## 7) What you will see in the console
- Whether the job ran successfully
- Each execution time
- Container logs and Python errors
- Job configuration

That is the cleanest way to make this visible in Google Cloud Console instead of only inside GitHub Actions.
