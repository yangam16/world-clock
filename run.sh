#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
world_clock_root=$PWD
export PYTHONPATH="$world_clock_root/src${PYTHONPATH:+:$PYTHONPATH}"
# Older installations retain their flat Python files. Start inside src so they
# cannot shadow the new package; the application resolves its data root itself.
cd -- "$world_clock_root/src"
exec /usr/bin/python3 -m world_clock "$@"
