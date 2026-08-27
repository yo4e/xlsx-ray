#!/bin/sh

set -eu

printf "\n=== XLSX-Ray first-run demo ===\n"
printf "This demo uses generated, non-sensitive workbooks and keeps XLSX-Ray local and read-only.\n"

printf "\n[1/3] Generate synthetic demo workbooks\n"
python examples/create_demo_workbooks.py

printf "\n[2/3] Review what changed\n"
printf "Look first at 'Changes', 'Highest risk', and the high-risk rows below.\n\n"
xlsx-ray diff examples/generated/before.xlsx examples/generated/after.xlsm

printf "\n[3/3] Verify the CI threshold\n"
printf "Re-running the same diff with --fail-on high. The duplicate report is hidden here; only the gate result matters.\n"
set +e
xlsx-ray diff examples/generated/before.xlsx examples/generated/after.xlsm --fail-on high >/dev/null
threshold_status=$?
set -e

if [ "$threshold_status" -ne 1 ]; then
    printf "ERROR: expected --fail-on high to exit 1, got %s\n" "$threshold_status" >&2
    exit 1
fi

printf "OK: --fail-on high exited 1 because a supported high-risk change was detected.\n"
printf "That exit 1 is the expected CI gate signal, not a failed inspection or broken demo.\n"
printf "\nDemo complete. Product semantics and risk thresholds were not changed.\n"
