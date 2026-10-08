#!/bin/sh
# Test-only sendmail replacement; writes locally and never contacts a provider.
set -eu
cat > /tmp/opigno-mail-fixture.eml
