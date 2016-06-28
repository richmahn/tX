#!/bin/sh

set x $(ps ax | grep -v grep | grep /var/www/vhosts/webhook/convert.py)

if [ $# -gt 2 ] ; then
  kill $2
fi

baseDir=/var/www/vhosts/webhook

[ -f convert.sh ] && cp convert.sh $baseDir && chown root:root convert.sh
[ -f convert.py ] && cp convert.py $baseDir && chown root:root convert.py
[ -f template.json ] && cp template.json $baseDir

cd $baseDir
#python $baseDir/convert.py 9096 >/var/log/convert.log 2>&1 < /dev/null &
python $baseDir/convert.py 9096 gogs 2>&1 < /dev/null &
#tail -f /var/log/convert.log
