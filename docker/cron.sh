#!/usr/bin/env bash
set -eu
while sleep "${CRON_INTERVAL:-300}"; do
  if ! /var/www/opigno/vendor/bin/drush --root=/var/www/opigno/web --uri="$SITE_URL" --quiet cron; then
    echo 'Opigno cron failed; retrying at the next interval.' >&2
  fi
done
