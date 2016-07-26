[![Build Status](https://travis-ci.org/unfoldingWord-dev/conv.door43.org.svg?branch=master)](https://travis-ci.org/unfoldingWord-dev/conv.door43.org)


# tX

A conversion app for the repos at git.door43.org.  Output ends up at [Door43](http://door43.org).
This app should:

 * accept a webhook notification from Gogs,
 * pull source content from respective Gogs repo
 * identify type of source content (USFM or Markdown) (possibly by reading manifest.json defined in http://discourse.door43.org/t/resource-containers/53, or by reading file extensions)
 * convert into a single HTML page
 * upload to door43 S3 bucket (at same relative URL from Gogs, with some tweaks: /u/[user]/[repo]/[short_commit_hash]/html/index.html)


## Python Requirements

Requirements for a Python script need to reside within the function's directory that calls them.  A requirement for the `convert` function should exist within `functions/convert/`.

The list of requirements for a function should be in a requirements.txt file within that function's directory, for example: functions/convert/requirements.txt.

Requirements *must* be installed before deploying to Lambda.  For example:

    pip install -r functions/convert/requirements.txt -t functions/convert/

The `-t` option tells pip to install the files into the specified target directory.  This ensures that the Lambda environment has direct access to the dependency.

If you have any Python files in subdirectories that also have dependencies, you can import the ones available in the main function by using `sys.path.append('/var/task/')`.

Lastly, if you install dependencies for a function you need to include the following in an .apexignore file:

    *.dist-info


