#!/bin/sh

set -eu

python examples/create_demo_workbooks.py

xlsx-ray diff examples/generated/before.xlsx examples/generated/after.xlsm

set +e
xlsx-ray diff examples/generated/before.xlsx examples/generated/after.xlsm --fail-on high
threshold_status=$?
set -e

printf "\n--fail-on high exit code: %s (expected: 1)\n" "$threshold_status"
if [ "$threshold_status" -ne 1 ]; then
    printf "demo validation failed: expected the supported high-risk findings to exit 1\n" >&2
    exit 1
fi
