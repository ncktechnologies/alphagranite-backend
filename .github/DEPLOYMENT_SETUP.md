# CI/CD Deployment Setup

This repository uses GitHub Actions to automatically deploy to your production server whenever you push to the `job` or `main` branches.

## Prerequisites

Before the CI/CD pipeline can work, you need to configure the following GitHub Secrets.

## Setting up GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add the following secrets:

### Required Secrets

| Secret Name | Value | Description |
|------------|-------|-------------|
| `VPS_HOST` | `93.114.128.181` | Your VPS server IP address |
| `VPS_USERNAME` | `root` | SSH username for your server |
| `VPS_SSH_KEY` | `<contents of your ssh_key file>` | Your private SSH key |

### How to get your SSH key content

Open your SSH key file and copy its entire contents:

```bash
cat ssh_key
```

Copy everything including:
- `-----BEGIN OPENSSH PRIVATE KEY-----`
- The key content
- `-----END OPENSSH PRIVATE KEY-----`

Paste the entire content as the value for `VPS_SSH_KEY` secret.

## How the CI/CD Works

### Trigger Events
- **Automatic**: Runs on every push to `job` or `main` branches
- **Manual**: You can also trigger it manually from the Actions tab

### Deployment Steps

The workflow automatically:

1. ✅ Checks out the latest code
2. ✅ Connects to your VPS via SSH
3. ✅ Checks if Docker is installed (installs if missing)
4. ✅ Checks if Docker Compose is installed (installs if missing)
5. ✅ Navigates to `/root/alphagranite/alpha-granit`
6. ✅ Pulls latest changes from Git
7. ✅ Cleans up Docker system (`docker system prune --force -a`)
8. ✅ Builds Docker images with no cache
9. ✅ Starts services in detached mode
10. ✅ Displays container status and recent logs

### Monitoring Deployments

1. Go to the **Actions** tab in your GitHub repository
2. Click on the latest workflow run
3. View real-time logs and deployment status
4. Check if deployment succeeded or failed

## Manual Deployment

If you need to manually trigger a deployment:

1. Go to **Actions** tab
2. Click on **Deploy to Production** workflow
3. Click **Run workflow**
4. Select the branch and click **Run workflow**

## Troubleshooting

### Deployment Fails

Check the workflow logs in the Actions tab to see what went wrong. Common issues:

- **SSH Connection Failed**: Check if `VPS_SSH_KEY` secret is correctly set
- **Git Pull Failed**: Ensure the server has access to the repository
- **Docker Build Failed**: Check the application logs for build errors
- **Permission Denied**: Ensure the SSH key has proper permissions on the server

### View Server Logs

SSH into your server and check logs:

```bash
ssh root@93.114.128.181 -i ssh_key
cd /root/alphagranite/alpha-granit
docker compose logs -f
```

## Environment Variables

Make sure your `.env` file is properly configured on the server at:
```
/root/alphagranite/alpha-granit/.env
```

This file should contain:
- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- Any other required environment variables

## Security Notes

- ⚠️ Never commit your SSH private key to the repository
- ⚠️ Never commit `.env` files with sensitive data
- ✅ Always use GitHub Secrets for sensitive information
- ✅ Rotate SSH keys periodically for security

## Support

For issues with the deployment pipeline, check:
1. GitHub Actions logs
2. Server Docker logs
3. Application logs at `/root/alphagranite/alpha-granit/logs/`
