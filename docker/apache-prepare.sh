#!/usr/bin/env bash
set -Eeuo pipefail

# mod_php requires prefork. Normalize at startup as well as image build time:
# a Railway deployment exposed a conflicting MPM at runtime.
a2dismod -f mpm_event mpm_worker
a2enmod mpm_prefork
apache2ctl -t
