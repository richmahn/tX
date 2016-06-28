Flask app for converting docs between various formats
#####################################################

/var/www/vhosts/webhook/convert.py main script
convert.sh utility to start listener

Gettings started
----------------

cp convert.py to /var/www/vhosts/webhook/
cp template.json to /var/www/vhosts/webhook/

Outline
-------

1) Repo Owner sets up notification
2) Service is started
3) recieves notification from gogs
4) Parses message for doc type
5) Reads template.json and looks up doc type
6) Applys transforms for doctype
7) Sends result to s3 as reponame.finalExt

