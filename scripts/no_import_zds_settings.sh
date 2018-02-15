#!/bin/sh -e

cd "$(dirname "$0")"

cd ../zds

search() {
    grep -rn zds | grep settings | grep import | grep -v '^settings' | grep -v 'get_hat_from_settings'
}

if ! search >/dev/null
then
   exit 0
fi

>&2 cat <<'EOF'

GOTCHA!

Don't import directly `zds.settings`, please import `django.conf`
instead.

Fix these lines:

EOF

>&2 search

exit 1
