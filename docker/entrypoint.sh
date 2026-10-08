#!/usr/bin/env bash
set -Eeuo pipefail

# Allow maintenance commands without starting the web server or installer.
if [[ "${1:-}" != 'apache2-foreground' ]]; then
  exec "$@"
fi

for name in MYSQLHOST MYSQLDATABASE MYSQLUSER MYSQLPASSWORD; do
  if [[ -z "${!name:-}" ]]; then
    echo "Required environment variable is missing: $name" >&2
    exit 1
  fi
done
export PORT="${PORT:-8080}"
if [[ ! "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
  echo 'PORT must be an integer between 1 and 65535.' >&2
  exit 1
fi
export SITE_URL="${SITE_URL:-${RAILWAY_PUBLIC_DOMAIN:+https://${RAILWAY_PUBLIC_DOMAIN}}}"
export SITE_URL="${SITE_URL:-http://localhost:8080}"
mkdir -p /data/{public,private,tmp,config}
chown www-data:www-data /data/{public,private,tmp,config}
chmod 0750 /data/{private,tmp,config}
chmod 0755 /data/public
if [[ -z "${DRUPAL_HASH_SALT:-}" && ! -s /data/hash-salt ]]; then
  (umask 027; php -r 'echo bin2hex(random_bytes(32));' > /data/hash-salt)
fi
if [[ -f /data/hash-salt ]]; then
  chown root:www-data /data/hash-salt
  chmod 0640 /data/hash-salt
fi
printf 'Listen %s\n' "$PORT" > /etc/apache2/ports.conf
/usr/local/bin/opigno-apache-prepare

state="$(php /usr/local/share/opigno/database-state.php)"
drush=(gosu www-data /var/www/opigno/vendor/bin/drush --root=/var/www/opigno/web --uri="$SITE_URL")
if [[ "$state" == 'empty' ]]; then
  for name in OPIGNO_ADMIN_PASSWORD OPIGNO_ADMIN_EMAIL; do
    if [[ -z "${!name:-}" ]]; then
      echo "First installation requires $name." >&2
      exit 1
    fi
  done
  echo 'Installing Opigno in the empty database. This can take several minutes.'
  "${drush[@]}" --quiet site:install opigno_lms --yes \
    --site-name="${OPIGNO_SITE_NAME:-Opigno LMS}" \
    --site-mail="$OPIGNO_ADMIN_EMAIL" \
    --account-name="${OPIGNO_ADMIN_USERNAME:-admin}" \
    --account-mail="$OPIGNO_ADMIN_EMAIL" \
    --account-pass="$OPIGNO_ADMIN_PASSWORD"
fi

# Fail on partial installations or unrelated databases without deleting data.
"${drush[@]}" --quiet php:script /usr/local/share/opigno/verify-install.php
# Rebuild derived assets after image changes (H5P mirrors vendor JS into /data).
"${drush[@]}" --quiet cache:rebuild
echo 'Opigno installation verified.'

if [[ "${CRON_ENABLED:-1}" == '1' ]]; then
  if [[ ! "${CRON_INTERVAL:-300}" =~ ^[1-9][0-9]*$ ]]; then
    echo 'CRON_INTERVAL must be a positive number of seconds.' >&2
    exit 1
  fi
  gosu www-data /usr/local/bin/opigno-cron &
fi
exec docker-php-entrypoint "$@"
