#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from urlparse import urljoin
from flask import Flask, redirect, render_template, send_file, url_for, request, flash
from werkzeug import secure_filename
from beefish import decrypt, encrypt
from models import File
import boto
from StringIO import StringIO
from urlparse import urljoin

def get_bucket(access_key_id, secret_access_key, bucket_name):
    conn = boto.connect_s3(access_key_id, secret_access_key)
    return conn.get_bucket(bucket_name)


def upload_handler(instance, file_obj):
    bucket = get_bucket(app.config['AWSID'], app.config['AWSKEY'], app.config['AWSBUCKET'])
    key = bucket.new_key(instance.filename)
    key.set_metadata('Content-Type', instance.get_mimetype())

    # new code here:

    if request.form.get('password'):
        # we received a password, so will need to encrypt the file data
        # before sending it off to S3
        password = request.form['password']
        instance.encrypted = True
        output_buffer = StringIO()
        encrypt(file_obj, output_buffer, password)
        file_obj = output_buffer
    else:
        instance.encrypted = False

    # end of new code

    file_obj.seek(0)
    key.set_contents_from_file(file_obj)
    key.set_acl('public-read')

DEBUG = True
SECRET_KEY = "kasjhdaskdhkasd8aksd78ad7"

AWSID = 'AKIAJEZ2S5HSPP3DQMLA'
AWSKEY = 'UXu5fv6/p2Ec/UyfCokFblNYcjgjDGxls6CGNqyk'
AWSBUCKET = 'enc-test'
AWSBUCKETURL = 'https://s3-eu-west-1.amazonaws.com/%s/' % AWSBUCKET

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def index():
    return render_template('index.html', files=File.select().order_by('filename'))

@app.route('/add/', methods=['POST'])
def add():
    if request.files['file']:
        file_obj = request.files['file']
        instance = File.get_or_create(filename=secure_filename(file_obj.filename))
        upload_handler(instance, file_obj)
        instance.save()
    else:
        flash("You did not choose a file! Try again")
    return redirect(url_for('index'))

@app.route('/download/<int:file_id>/', methods=['GET', 'POST'])
def download(file_id):
    try:
        file = File.get(id=file_id)
    except File.DoesNotExist:
        abort(404)

    if not file.encrypted:
        return redirect(urljoin(app.config['AWSBUCKETURL'], file.filename))

    # new logic:
    if request.method == 'POST' and request.form.get('password'):
        # fetch the encrypted file contents from S3 and store in a memory
        bucket = get_bucket(app.config['AWSID'], app.config['AWSKEY'], app.config['AWSBUCKET'])
        key_obj = bucket.get_key(file.filename)

        # read the contents of the key into an in-memory file
        enc_buffer = StringIO()
        key_obj.get_contents_to_file(enc_buffer)
        enc_buffer.seek(0)

        # decrypt contents and store in dec_buffer
        dec_buffer = StringIO()
        decrypt(enc_buffer, dec_buffer, request.form['password'])
        dec_buffer.seek(0)

        # efficiently send the decrypted file as an attachment
        return send_file(
            dec_buffer,
            file.get_mimetype(),
            as_attachment=True,
            attachment_filename=file.filename,
        )

    # display a password form
    return render_template('download.html', file=file)

@app.route('/delete/<int:file_id>/')
def delete(file_id):
    try:
        file = File.get(id=file_id)
    except File.DoesNotExist:
        abort(404)
    bucket = get_bucket(app.config['AWSID'], app.config['AWSKEY'], app.config['AWSBUCKET'])
    key_obj = bucket.get_key(file.filename)
    if key_obj:
        try:
            key_obj.delete()
        except:
            flash("There was an error deleting your file from S3!")
    file.delete_instance()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
