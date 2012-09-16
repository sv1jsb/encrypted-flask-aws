## Web-based encrypted file storage using Flask and AWS

This repository was created from Charles Leifer's excellent [article](http://charlesleifer.com/blog/web-based-encrypted-file-storage-using-flask-and-aws/) on how to use flask, boto and pycrypto to have your files encrypted and uploaded to Amazon's S3.


You will need to provide the following in app.py in order to be able to use S3.

    AWSID = '<your AWS key id>'
    AWSKEY = '<your AWS key secret>'
    AWSBUCKET = '<your bucket name>'

For first time run you can create the database by starting a python shell at the directory where app.py is and issuing the commands:

    >>> from app import create_tables
    >>> create_tables()

I have made a few additions to the article.

* Files can be deleted.
* Files with the same name are updated.
* Folder creation and deletion.
* Search for files or folders.
* All files/folders are private.


Added also the [bootstrap](http://twitter.github.com/bootstrap/index.html) css and javascript.

Have fun!

Andreas
