#!/usr/bin/env python

# get required code
import os
import sys
import json
import requests
import ipaddress
import logging
import time
import subprocess
import boto3

from datetime import date
from logging.handlers import RotatingFileHandler
from flask import Flask, request, Response #, abort

MAXJSON  = 10000

# define file paths
baseDir  = '/var/www/vhosts/'
toolsDir = baseDir + 'door43.org/tools/general_tools'
appDir   = baseDir + 'conv.door43.org/'
workDir  = appDir  + 'data/'
outDir   = appDir  + 'output/'
logFile  = '/var/log/convert.log'
bucket   = 's3://door43.org/u/' # pusher repo hash fmt
config   = '/root/.s3-convert.cfg'

sys.path.append( toolsDir )

app = Flask(__name__) # begin flask app

# set up logging
app.logger.setLevel( logging.INFO )
handler = RotatingFileHandler( logFile, maxBytes=1024 * 1024* 100, backupCount=5 )
handler.setLevel( logging.INFO )
app.logger.addHandler( handler )
app.logger.info( "Start" )

try:
    from git_wrapper import *
except:
    app.logger.warn( "Missing: " + toolsDir )
    sys.exit(1)

try: # template of things to do based on repo
   #template = json.load( urllib2.urlopen( "template.json" ) )
   tmp = open( "template.json", "r" )
   tmpRaw = tmp.read( MAXJSON )
   tmp.close()
   templates = json.loads( tmpRaw )
   app.logger.info( "  templates: " + tmpRaw )
except:
   app.logger.error( "Cannot read transform template" )
   sys.exit( 2 )

app.logger.info( "Using: " + sys.argv[ 2 ] )

if sys.argv[ 2 ] == "gogs": # get request from gogs
    @app.route( "/", methods=[ 'GET', 'POST' ] )  # bind to next function
    def index():
        if request.method == 'GET':
            return 'Testing, Testing: 1, 2, 3. Its all good.'

        elif request.method == 'POST':
            app.logger.info( "  Is request post" )

            # get repo notification
            app.logger.info( request.data )
            payload = json.loads( request.data )
            res = proc( payload )
            app.logger.info( res )
            #resp = app.make_response()
            #resp.status = res
            return Response( "Result" ), res

if sys.argv[ 2 ] == "sqs": # get request from aws queue
    sqs = boto3.resource( 'sqs' )

    # Get the queue. This returns an SQS.Queue instance
    queue = sqs.get_queue_by_name( QueueName='convert' )

    app.logger.info( json.dumps( queue ) )

    for message in queue.receive_messages( MessageAttributeNames=['Author'] ):
        # Get the custom author message attribute if it was set
        author_text = ''
        if message.message_attributes is not None:
            author_name = message.message_attributes.get('Author').get('StringValue')
            if author_name:
                author_text = ' ({0})'.format(author_name)

        # Print out the body and author (if set)
        print('Hello, {0}!{1}'.format(message.body, author_text))

        res = proc( payload )

        # Let the queue know that the message is processed
        message.delete()

def proc( payload ): # process request from wherever
    repoName = payload['repository']['name']
    app.logger.info( "  name: " + repoName )

    cloneUrl = payload['repository']['clone_url']
    app.logger.info( "  clone_url: " + cloneUrl )

    localPath = workDir + repoName
    app.logger.info( "  localPath: " + localPath )

    s = '/'
    pusher = payload[ 'pusher' ][ 'username' ] + s
    hash = payload[ 'commits' ][0][ 'id' ][:8] + s
    dest =  pusher + repoName + s + hash
    app.logger.info( "dest: " + dest )

    # get collection from repo
    try:
        # setup git
        if not os.path.exists( workDir ):
            os.path.mkdirs( workDir, exist_ok=True )
    except:
        app.logger.error( "Cannot access source directory: " + workDir )
        app.logger.info( "  In: " + workDir )

    os.chdir( workDir )

    try: # git clone/pull
        if os.path.exists( repoName ): #  then pull
            os.chdir( repoName )
            cmd = "git pull"
            res = subprocess.check_output( cmd, shell=True )
        else: # clone
            cmd = "git clone " + cloneUrl + " " + repoName
            res = subprocess.check_output( cmd, shell=True )
            os.chdir( repoName )

        app.logger.info( cmd )
        app.logger.info( res )
        res = subprocess.check_output( "ls -l", shell=True )
        app.logger.info( res )

    except:
        app.logger.error( "Cannot: " + cmd + ": " + cloneUrl )
        return "501"

    os.chdir( workDir + repoName )
    app.logger.info( "  pwd: " + os.getcwd() )

    try: # look at repo manifest
        #app.logger.info( "try to parse manifest" )

        # read manifest
        if os.path.isfile( "manifest.json" ):
            mf = open( "manifest.json", "r" )
            raw = mf.read( MAXJSON )
            mf.close()
            app.logger.info( "have manifest" + raw )
            manifest = json.loads( raw )
        else:
            app.logger.error( "No manifest for this repo." )
            return "502"

        # Identify doc type
        inputFormat = manifest[ 'format' ]
        app.logger.info( "  format: " + inputFormat )

        docType = manifest[ 'source_translations' ][0][ 'resource_id' ]
        app.logger.info( "  docType: " + docType )

    except:
        app.logger.error( "Cannot parse manifest" )
        return "503"

    try: # Find doctype in template then process per template
        isFound = False
        app.logger.info( "  looking for docType: " + docType )

        for item in templates[ 'templates']:
            app.logger.info( "  trying: " + item['doctype'] )
            
            if item['doctype'] == docType:
                app.logger.info( "  found: " + item['doctype'] )

                try: # Apply qualifying tests
                    for test in item[ 'tests' ]:
                        app.logger.info( test )
                        #invoke test
                except:
                    app.logger.warning( "  Cannot apply tests" )

                try: # apply transforms from template
                    for trans in item[ 'transforms' ]:
                        app.logger.info( trans )
                        #tool = "python " + appDir + "converters/" + trans[ 'tool' ]
                        tool = appDir + "converters/" + trans[ 'tool' ]
                        source = trans[ 'to' ]
                        src = workDir + repoName
                        tgt = outDir + dest + source
                        cmd = tool + " -s " + src + " -d " + tgt
                        app.logger.info( 'cmd: ' + cmd )
                        res = subprocess.check_output( cmd, shell=False )
                        app.logger.info( 'result: ' + res )
                except:
                    app.logger.warning( "  Cannot apply transforms" )

                isFound = True
                break

        if isFound == False:
            app.logger.error( "Cannot find docType: " + docIdx )
            return "504"

    except:
        app.logger.error( "No support for docType: " + docType )
        return "505"

    try: # Upload to s3
        cfg = "-c " + config
        outPath = bucket + dest
        cmd = "s3cmd put -r " + cfg + " -f " + tgt + " " + outPath
        app.logger.info( cmd )
        res = subprocess.check_output( cmd, shell=True )
        app.logger.info( res )
        #res = subprocess.Popen( [ "rm -r ", src ] )

    except:
        app.logger.warning( "Cannot upload to s3" )
        return "506"

    return '200'

if __name__ == "__main__":
    try:
        port_number = int(sys.argv[1])
    except:
        port_number = 80

    is_dev = os.environ.get('ENV', None) == 'dev'

    if os.environ.get('USE_PROXYFIX', None) == 'true':
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

    app.run( host='0.0.0.0', port=port_number, debug=is_dev )


