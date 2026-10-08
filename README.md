# Opigno LMS on Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/Ys283P)

Deploy a custom fork of **Opigno LMS 3.2.7** with Docker. Includes Drupal 10,
CKEditor 5, updated PDF tools, private MySQL 8.4, persistent storage, and optional
Resend email delivery.

[Build status](https://github.com/aghoukad/opigno-railway/actions/workflows/validate.yml) ·
[Version and maintenance details](MAINTENANCE.md) ·
[Validation results](reports/validation.md)

## Deploy on Railway

1. Click **Deploy on Railway** above.
2. Enter `OPIGNO_ADMIN_EMAIL` and deploy both services.
3. Wait for the build and installation to finish; the first start takes several minutes.
4. Open the Opigno service's public URL and go to `/user/login`.
5. Sign in with username `admin` and the generated `OPIGNO_ADMIN_PASSWORD` from
   **Opigno → Variables**.

The template creates a public HTTPS URL for Opigno on port **8080** and keeps
MySQL private. Database passwords and the Drupal hash salt are generated for each
deployment. Uploads persist in `/data`; MySQL data persists in `/var/lib/mysql`.

Administrator variables apply only to the first installation. Changing them later
does not reset an existing account.

## Email with Resend

Verify your sending domain in [Resend](https://resend.com/domains), then set these
in **Opigno → Variables** and deploy the changes:

| Variable | Value |
| --- | --- |
| `RESEND_API_KEY` | Your Resend sending API key |
| `RESEND_FROM_EMAIL` | Address on your verified domain, such as `notifications@yourdomain.com` |
| `RESEND_FROM_NAME` | Optional sender name; defaults to `Opigno LMS` |

The key and sender are blank placeholders. Leave **both** blank to run without
email, or configure **both** to enable it. Setting only one prevents startup.
Keep the real key in Railway variables or your local `.env`, never in Git.

Email uses Resend's HTTPS API and supports HTML and attachments. Test delivery to
an address you control before enabling account notifications or password resets.

## Run locally

```sh
cp .env.example .env
```

Edit `.env`: set `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`,
`OPIGNO_ADMIN_PASSWORD`, and `OPIGNO_ADMIN_EMAIL`. Use a different random password
for each account; `openssl rand -hex 32` can generate one.

```sh
docker compose up -d --build
docker compose logs -f opigno
```

Once installation finishes, open **http://localhost:8080** and sign in with
`admin` and your `OPIGNO_ADMIN_PASSWORD`. Set `LOCAL_PORT` in `.env` if port 8080
is already in use. Resend variables are optional locally too.

## Domains and troubleshooting

For a custom domain, set `SITE_URL=https://learning.example.com` and redeploy.
If Drupal reports **"The provided host name is not valid for this server"**, set
`SITE_URL` to your exact public HTTPS URL and redeploy. The hostname is then
allowed automatically. Additional aliases go in `DRUPAL_TRUSTED_HOSTS`, separated
by commas without `https://`.

If email is unavailable, check that both Resend variables are set and the sending
domain is verified. The readiness endpoint is `/healthz.php`.

## Maintenance

- Back up MySQL and `/data` together, and test restoring them. Keep volumes and
  generated secrets across redeployments.
- Test upgrades on a copy of your data. Startup preserves an installed database;
  it does not automatically run database migrations.
- **Drupal 10 support ends December 9, 2026.** Plan the Drupal 11 migration using
  the [maintenance guide](MAINTENANCE.md).

See the [Railway reference](railway/README.md) for template customization, service
icons, email transport details, and operational settings. Review the
[validation results](reports/validation.md) for tested features and remaining
production checks.
