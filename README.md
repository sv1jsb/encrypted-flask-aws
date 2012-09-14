## Web-based encrypted file storage using Flask and AWS

This repository was created from Charles Leifer's excellent [article](http://charlesleifer.com/blog/web-based-encrypted-file-storage-using-flask-and-aws/) on how to use flask, boto and pycrypto to have your files encrypted and uploaded to Amazon's S3.


You will need to provide the following in app.py in order to be able to use S3.

    AWSID = '<your AWS key id>'
    AWSKEY = '<your AWS key secret>'
    AWSBUCKET = '<your bucket name>'

I have made a few corrections from the article. I also don't make the files public and use boto to download them. Added also the [bootstrap](http://twitter.github.com/bootstrap/index.html) css and javascript.

Have fun!

Andreas
