#!/usr/bin/env bash
set -e
path="."
test -z "$1" || path="$1"
for file in $(find "${path}" -name "*.py"); do
    echo "(pep8) >> $file"
    autopep8 --in-place --aggressive --aggressive "${file}"
done
exit $?
