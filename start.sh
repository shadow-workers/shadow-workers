#!/bin/bash
if [ ! -f ./private_key.pem ]; then
  vapid --gen
fi
if [ ! -f ./.password ]; then
  (export LC_CTYPE=C ; cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1 > .password)
fi
if [ ! -f ./.agenttoken ]; then
  (export LC_CTYPE=C ; cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1 > .agenttoken)
fi
flask db upgrade
mitmweb -k -s sw_mitm.py -p 8888 --no-web-open-browser &
python c2.py && fg
