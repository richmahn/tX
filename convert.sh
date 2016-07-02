#!/bin/sh
######################################################################
#
# NAME convert.sh  -  Start conversion flask server
#
  USAGE="convert.sh -h|--help|restart|start|stop"
#
######################################################################

baseDir=/var/www/vhosts/conv.door43.org

case $1 in
  -h|--help)
    echo "Usage: $USAGE"
    exit 0
    ;;

  restart|stop)
    set x $(ps ax | grep -v grep | grep $baseDir/convert.py)

    if [ $# -gt 2 ] ; then
      kill $2
    fi
    
    sleep 2
    ;;

  restart|start)
    cd $baseDir
    python $baseDir/convert.py 9096 gogs 2>&1 < /dev/null &
    #python $baseDir/convert.py 9096 >/var/log/convert.log 2>&1 < /dev/null &
    #tail -f /var/log/convert.log
    ;;
  
  install) 
    #baseDir=/var/www/vhosts/webhook
    #cd $baseDir
    #convDir=$baseDir/converters
    #obsDir=$convDir/obs/templates
    #taDir=$convDir/ta/templates
    #[ -f convert.sh ] && cp convert.sh $baseDir && chown root:root convert.sh
    #[ -f convert.py ] && cp convert.py $baseDir && chown root:root convert.py
    #[ -f template.json ] && cp template.json $baseDir
    #
    #[ -d $obsDir ] || mkdir -p $obsDir
    #[ -f converters/obs/convert_to_html.py ] && \
    #    cp converters/obs/convert_to_html.py  $baseDir/converters/obs && \
    #    cp converters/obs/templates/* $baseDir/converters/obs/templates
    #chmod +x $baseDir/converters/obs/convert_to_html.py
    #
    #[ -d $taDir ] || mkdir -p $taDir
    #[ -f converters/ta/convert_to_html.py ] && \
    #    cp converters/ta/convert_to_html.py  $baseDir/converters/ta && \
    #    cp converters/ta/templates/* $baseDir/converters/ta/templates
    #chmod +x $baseDir/converters/ta/convert_to_html.py
    ;;

  "")
    echo "Missing action."
    echo "Usage: $USAGE"
    exit
    ;;

  *)
    echo "Invalid argument: $1"
    echo "Usage: $USAGE"
    exit 1
    ;;
esac


