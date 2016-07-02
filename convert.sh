#!/bin/sh
######################################################################
#
# NAME convert.sh  -  Start conversion flask server
#
  USAGE="convert.sh -h|--help|init|install|log|restart|start|stop
  Where:
    -h|--help  Display this text
    init       install, restart, log
    install    Make necessary run time directories
    log        Show current log in real time
    restart    Stop then start server process
    start      Start server process
    stop       Kill server process"
#
######################################################################

baseDir=/var/www/vhosts/conv.door43.org

install() {
  mkdir -p -v $baseDir/{data,output} 
  chmod +x $baseDir/converters/*/*.py
}


log() {
  tail -n 100 -f /var/log/convert.log 
}


start() {
  cd $baseDir
  python $baseDir/convert.py 9096 gogs >/var/log/convert.log 2>&1 < /dev/null &
}


stop() {
  set x $(ps ax | grep -v grep | grep $baseDir/convert.py)

  if [ $# -gt 2 ] ; then
    kill $2
  fi
    
  sleep 2
}


case $1 in
  -h|--help)
    echo "Usage: $USAGE"
    exit 0
    ;;

  restart) stop     ; start ;; 
  stop)    stop    ;; 
  start)   start   ;; 
  log)     log     ;;
  init)    install  ; stop ; start ; log ;;
  install) install ;;

  "")
    echo "Missing action."
    echo "Usage: $USAGE"
    exit 1
    ;;

  *)
    echo "Invalid argument: $1"
    echo "Usage: $USAGE"
    exit 1
    ;;
esac

exit 0
