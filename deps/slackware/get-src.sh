#!/bin/sh

#set -e -x

GREP=$(which grep)
WGET=$(which wget)

for d in $(ls -d */)
do
  cd $d  
  $WGET -c -nd -nH `$GREP "DOWNLOAD=" *.info | sed 's|DOWNLOAD="\(.*\)"|\1|'`
  cd ..
done



