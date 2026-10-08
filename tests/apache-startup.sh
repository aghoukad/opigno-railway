#!/usr/bin/env bash
set -Eeuo pipefail

# Run only inside a disposable container. Reproduce the Railway startup failure
# by adding conflicting MPMs without a2enmod's conflict protection.
for module in mpm_event mpm_worker; do
  ln -sf "../mods-available/${module}.load" "/etc/apache2/mods-enabled/${module}.load"
done
if apache2ctl -t > /tmp/apache-check.log 2>&1; then
  echo 'Expected the conflicting MPM fixture to fail.' >&2
  exit 1
fi
grep -q 'More than one MPM loaded' /tmp/apache-check.log

/usr/local/bin/opigno-apache-prepare
/usr/local/bin/opigno-apache-prepare
modules="$(apache2ctl -M)"
printf '%s\n' "$modules" | grep -q 'mpm_prefork_module'
if printf '%s\n' "$modules" | grep -Eq 'mpm_(event|worker)_module'; then
  echo 'An incompatible MPM is still loaded.' >&2
  exit 1
fi
printf '%s\n' "$modules" | grep -q 'php_module'
echo 'Apache startup recovers from conflicting MPMs and remains idempotent.'
