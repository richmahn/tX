# conv.door43.org

A conversion platform for the [Door43](http://door43.org) website.
This app should:

 * accept a webhook notification from Gogs,
 * pull source content from respective Gogs repo
 * identify type of source content (USFM or Markdown) (possibly by reading manifest.json defined in http://discourse.door43.org/t/resource-containers/53, or by reading file extensions)
 * convert into a single HTML page
 * upload to door43 S3 bucket (at same relative URL from Gogs, with some tweaks: /u/[user]/[repo]/[short_commit_hash]/html/index.html)

