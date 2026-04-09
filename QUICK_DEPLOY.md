# Quick Deploy

## Best handoff approach
The best handoff is **both**:
1. a detailed setup guide
2. an **Open in Cloud Shell** button

Why both?
- A real single-click deploy still cannot supply Kevin's OAuth credentials, refresh token, SMTP password, domains, or DKIM selectors for him.
- An Open in Cloud Shell link gets him very close: it opens the repo directly in Google Cloud Shell with Google Cloud tools preinstalled, so he can deploy from the browser without local setup.

Google documents the **Open in Cloud Shell** feature for GitHub repositories and supports links that clone a repository directly into Cloud Shell. Cloud Shell also comes with the Google Cloud CLI already installed and authenticated for the signed-in user.

## Open in Cloud Shell
Use this link:

```text
https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/Sid3548/KProjects.git&cloudshell_open_in_editor=SETUP_GCP.md&cloudshell_print=HANDOFF.md&cloudshell_workspace=.&show=ide%2Cterminal&ephemeral=true
```

Or use this markdown button in docs:

```md
[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/Sid3548/KProjects.git&cloudshell_open_in_editor=SETUP_GCP.md&cloudshell_print=HANDOFF.md&cloudshell_workspace=.&show=ide%2Cterminal&ephemeral=true)
```

## What Kevin still needs to provide
Even with the Cloud Shell button, Kevin must still enter:
- OAuth client ID
- OAuth client secret
- refresh token
- sender email
- SMTP username/password
- recipient emails
- domains to monitor
- DKIM selectors

## Recommendation
Use the detailed docs as the primary handoff.
Use the Open in Cloud Shell button as the convenience entrypoint.

That is the closest thing to a single deploy button that still works honestly.
