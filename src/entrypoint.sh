#!bin/sh
if [ ! -f db.sqlite3 ]; then
    python3 -m flask db init
    python3 -m flask db migrate
    python3 -m flask db upgrade
    python3 -m flask api download_stars
fi
exec "$@"