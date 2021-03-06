#!/usr/bin/env python

# get required code
import os
import sys
import json
import logging
import time
import subprocess
import boto3

from boto3.session    import Session
from os.path          import join, getsize
from subprocess       import Popen, STDOUT, PIPE
from datetime         import date
from logging.handlers import RotatingFileHandler

debugLevel = 3

def myLog( level, msg):
    # micro debug
    sw = {
      "debug"   : 4,
      "info"    : 3,
      "warning" : 2,
      "error"   : 1
    }

    l = sw.get( level, 5 )

    if l <= debugLevel:
        print ( "  " * l ) + level + " " + msg

MAXJSON  = 10000
AWS_KEY = "AKIAIF6YW5V4KLGLAFSQ"
AWS_SECRET = "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"
AWS_REGION = "us-east-1"

# define file paths
baseDir  = '/tmp/'
appDir   = baseDir
workDir  = appDir 
outDir   = appDir  + 'output/'
bucket   = 'door43.org' # pusher repo hash fmt
config   = './.s3-convert.cfg'

try: # template of things to do based on repo
   tmp = open( "template.json", "r" )
   tmpRaw = tmp.read( MAXJSON )
   tmp.close()
   templates = json.loads( tmpRaw )
   myLog( "info", "templates: " + tmpRaw )
except:
   myLog( "error", "Cannot read transform template" )
   sys.exit( 2 )

# decode received message
sp = " "
lines = sys.stdin.readlines()
payload = json.loads( sp.join( lines ) )
repoName = payload['repository']['name']
myLog( "info", "name: " + repoName )

commitUrl = payload['commits'][0]['url'] 
commitUrl += ".tar.gz"
url = commitUrl.replace( "commit", "archive" )

# verify that url is from git.door43.org
if url.find( "git.door43.org" ) < 0:
    myLog( "warning", "Notification is not from Gogs. Ignoring." )
    print "400"
    sys.exit( 0 )

myLog( "info", "url: " + url )

localPath = workDir + repoName
myLog( "info", "localPath: " + localPath )

s = '/'
pusher = payload[ 'pusher' ][ 'username' ] + s
hash = payload[ 'commits' ][0][ 'id' ][:8] + s
dest =  pusher + repoName + s + hash
myLog( "info", "dest: " + dest )

# get collection from repo
zipDir = workDir + repoName
zipFile = zipDir + ".tar.gz"
myLog( "info", "  workDir: " + zipDir )
myLog( "info", "  zipFile: " + zipFile )
orgUmask = os.umask( 0 )

try:
    myLog( "info", "./curl " + url + " -o " + zipFile )
    res = subprocess.check_output( 
        [ "./curl", url, "-o", zipFile ], 
        shell=False )

    try:
        if not os.path.exists( zipDir ):
            os.makedirs( zipDir, 0777 )
 
        try:
             res = subprocess.check_output( 
                 [ "./tar", "-xzf", zipFile, "-C", zipDir ], 
                 shell=False )
        except OSError, e:
            myLog( "error", "cannot tar: " + zipFile +  " Error: " + e.strerror )
            print "506"
            sys.exit( 6 )
    except OSError, e:
        myLog( "error", "Cannot make working directory: " + zipDir + " Error: " + e.strerror )
        print "507"
        sys.exit( 7 )
except OSError, e:
    myLog( "error", "Cannot: curl " + url + " -o " + zipFile + " Error: " + e.strerror )
    print "508"
    sys.exit( 8 )

# check for manifest
os.umask( orgUmask )
orgDir = os.getcwd()
os.chdir( zipDir )
myLog( "info", "pwd: " + os.getcwd() )

if debugLevel > 3:
    for root, dirs, files in os.walk( "." ):
        myLog( "debug", "root: " + root )
        i = 5

        for nme in files:
            srcPath =  join( root, nme )
            myLog( "info", srcPath  )
            #i -= 1

            #if i < 1:
            #    sys.exit(0)

try: # look at repo manifest could be in subdirectory
    mani = "manifest.json"
    myLog( "info", "try to parse:" + mani )
    isMan = "no"

    # read manifest
    if os.path.isfile( mani ):
        mf = open( mani, "r" )
        isMan = "yes"
    elif os.path.isfile( repoName + "/" + mani ):
        mf = open(  repoName + "/" + mani, "r" )
        workDir += repoName + "/"
        isMan = "yes"

    if isMan == "yes":
        raw = mf.read( MAXJSON )
        mf.close()
        myLog( "debug", "have manifest" + raw )
        manifest = json.loads( raw )
    else:
        myLog( "error", "No manifest for this repo." )
        print "502"
        sys.exit( 2 )

    # Identify doc type
    inputFormat = manifest[ 'format' ]
    myLog( "info", "format: " + inputFormat )

    docType = manifest[ 'source_translations' ][0][ 'resource_id' ]
    myLog( "info", "docType: " + docType )

except OSError, e:
    myLog( "error", "Cannot parse manifest. Error: " + e.strerror )
    print "503"
    sys.exit( 3 )

try: # Find doctype in template then process per template
    isFound = False
    myLog( "info", "looking for docType: " + docType )

    for item in templates[ 'templates']:
        myLog( "info", "trying: " + item['doctype'] )

        if item['doctype'] == docType:
            myLog( "info", "found: " + item['doctype'] )

            try: # Apply qualifying tests
                for test in item[ 'tests' ]:
                    myLog( "info", test )
                    #invoke test
            except:
                myLog( "warning", "  Cannot apply tests." )

            try: # apply transforms from template
                for trans in item[ 'transforms' ]:
                    myLog( "debug", "  tool: " + trans[ 'tool' ] )
                    myLog( "debug", "  orgDir: " + orgDir + " current: " + os.getcwd() )
                    os.chdir( orgDir )
                    myLog( "info", "pwd: " + os.getcwd() )
                    tool =  "converters/" + trans[ 'tool' ]
                    source = trans[ 'to' ]
                    myLog( "info", "to: " + trans[ 'to' ] )
                    src = workDir + repoName
                    tgt = outDir + dest + source
                    cmd =  " -s " + src + " -d " + tgt
                    myLog( "info", "cmd: " + tool + " " + cmd )

                    try:
                       res = subprocess.check_output( 
                            [ "python", tool, "-s", src, "-d", tgt ],
                            stderr=subprocess.STDOUT,
                            shell=False )
                       myLog( "debug", 'tool result: ' +  res )
                    except OSError, e:
                        myLog( "warning", "Cannot run tool: " + tool + " " + cmd + ". Error: " + e.strerror )
            except:
                myLog( "warning", "  Cannot apply transforms" )

            isFound = True
            break

    if isFound == False:
        myLog( "error", "Cannot find docType: " + docIdx )
        print "504"
        sys.exit( 4 )

except:
    myLog( "error", "No support for docType: " + docType )
    print "505"
    sys.exit( 5 )

try: # Upload to s3
    myLog( "info", "About to ls" )
    os.chdir( outDir )
    src = dest # like "bspidel/gaj-x-ymnk_obs_text_obs/d2bc0dcb/html"
    outPath = bucket + dest

    session = Session( 
        aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET, 
        region_name=AWS_REGION 
    )

    s3 = session.client( 's3' )
    tpl = 1

    for root, dirs, files in os.walk( src ):
        myLog( "debug", "root: " + root )
        c = 1

        for nme in files:
            srcPath =  join( root, nme )
            myLog( "debug", "first srcPath: " + srcPath )  
            s3.upload_file( srcPath, bucket, "u/" + srcPath )
            myLog( "info", "From: " + srcPath + " to: s3://" + bucket + "/u/"  + srcPath )
            c += 1
        
        tpl += c
    myLog( "info",  "Files: " + str( tpl ))

except OSError, e:
    myLog( "warning", "Cannot upload to s3. Error: " + e.strerror  )
    print "506"

print '200'

if __name__ == "__main__":
    try:
        port_number = int(sys.argv[1])
    except:
        port_number = 80

    is_dev = os.environ.get('ENV', None) == 'dev'

    if os.environ.get('USE_PROXYFIX', None) == 'true':
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

    #app.run( host='0.0.0.0', port=port_number, debug=is_dev )


