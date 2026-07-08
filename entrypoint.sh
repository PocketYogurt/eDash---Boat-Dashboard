#!/bin/sh
set -eu

mkdir -p /usr/share/nginx/html

# HTML files no longer contain API keys — those are served by the API
# container at runtime via /api/me/config. Just copy static files.
cp /templates/index.html    /usr/share/nginx/html/index.html
cp /templates/planner.html  /usr/share/nginx/html/planner.html
cp /templates/login.html    /usr/share/nginx/html/login.html
cp /templates/admin.html    /usr/share/nginx/html/admin.html
cp /templates/trips.html    /usr/share/nginx/html/trips.html
cp /templates/profile.html  /usr/share/nginx/html/profile.html
cp /templates/auth.js       /usr/share/nginx/html/auth.js
cp /templates/manifest.json /usr/share/nginx/html/manifest.json
cp -r /templates/icons      /usr/share/nginx/html/icons
cp /templates/nginx.conf.template /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
