#!/bin/sh
# Usage: NOMULAB_ROOT=/path/to/site sh run_all.sh   (work files go to the current directory)
set -e
H=$(dirname "$0")
python3 "$H/extract.py"            # -> en.json / zh.json (title, body text, date per post)
python3 "$H/build_en.py"           # -> en_new.json (new headline per duplicated EN post)
python3 "$H/build_zh.py"           # -> zh_new.json
python3 "$H/run_en.py"             # rewrite EN posts + link labels
python3 "$H/run_zh.py"             # rewrite zh-TW posts + link labels
python3 "$H/add_og.py"             # og:image / twitter:card / JSON-LD image
