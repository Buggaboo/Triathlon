#!/bin/sh

#set -e -x

for f in `ls -d */ | sed 's|/$||'`
do
  ls -1 /tmp/$f*.tgz 2> /dev/null || echo "Uncompiled: $f"
done
