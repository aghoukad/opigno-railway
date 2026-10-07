#!/usr/bin/env bash
set -uo pipefail
status=0
composer --no-plugins audit --locked --no-dev || status=1
php /usr/local/share/opigno/check-assets.php composer.lock || status=1
if (( status != 0 )); then
  echo 'Production build blocked. See MAINTENANCE.md; dependency checks must pass before deployment.' >&2
fi
exit "$status"
