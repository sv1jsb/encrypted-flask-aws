#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from flask import Flask, redirect, render_template, send_file, url_for, request, flash, session, abort
from werkzeug.utils import secure_filename
from beefish import decrypt, encrypt
import boto
from StringIO import StringIO
from peewee import *
import mimetypes
import datetime
import os.path

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DEBUG = True
SECRET_KEY = "kas45hdas67dhkasd8aksd78ad7"
DATABASE = os.path.join(PROJECT_ROOT,'db.db')

AWSID = '<your AWS key id>'
AWSKEY = '<your AWS key secret>'
AWSBUCKET = '<your bucket name>'

app = Flask(__name__)
app.config.from_object(__name__)
database = SqliteDatabase(DATABASE)

class File(Model):
    class Meta:
        database = database
        
    filename = CharField()
    created_date = DateTimeField(default=datetime.datetime.now)
    encrypted = BooleanField(default=False)
    folder = BooleanField(default=False)
    parent = CharField(null=True)
    
    def get_mimetype(self):
        return mimetypes.guess_type(self.filename)[0]

def get_bucket(access_key_id, secret_access_key, bucket_name):
    conn = boto.connect_s3(access_key_id, secret_access_key)
    return conn.get_bucket(bucket_name)

def create_tables():
    database.connect()
    File.create_table()

def upload_handler(instance, file_obj):
    bucket = get_bucket(app.config['AWSID'], app.config['AWSKEY'], app.config['AWSBUCKET'])
    key = bucket.new_key(os.path.join(instance.parent,instance.filename))
    if instance.get_mimetype():
        key.set_metadata('Content-Type', instance.get_mimetype())

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

    file_obj.seek(0)
    key.set_contents_from_file(file_obj)


@app.route('/')
def index():
    if request.args.get('folder',None):
        folder = request.args.get('folder')
        session['folder'] = os.path.join('/',folder)
    else:
        session['folder'] = '/'
    files = File.filter(parent=session['folder']).order_by((File,'folder','DESC'),(File,'filename'))
    if session['folder'].endswith('/'):
        path=session['folder']
    else:
        path=session['folder']+'/'
    tmp = path[:-1].split('/')
    breads = []
    for i in range(1,len(tmp)+1):
        breads.append({'url':'/'.join(tmp[0:i]),'name':tmp[i-1]})
    breads[0]={'url':'/','name':'Home'}
    return render_template('index.html', files=files, breads=breads, path=path)

@app.route('/add/', methods=['POST'])
def add():
    if request.files['file']:
        file_obj = request.files['file']
        instance = File.get_or_create(parent = session['folder'], filename = secure_filename(file_obj.filename))
        try: 
            upload_handler(instance, file_obj)
        except:
            instance.delete_instance()
            flash("Uploading file failed!")
        else:
            instance.save()
    else:
        flash("You did not choose a file! Try again.")
    return redirect(url_for('index')+'?folder=%s'%session['folder'])

@app.route('/mkdir/', methods=['POST'])
def mkdir():
    if request.form.get('directory'):
        instance = File(parent=session['folder'],folder=True,filename = secure_filename(request.form.get('directory')))
        instance.save()
    else:
        flash("You did not provide a directory name! Try again.")
    return redirect(url_for('index')+'?folder=%s'%session['folder'])

@app.route('/download/<int:file_id>/', methods=['GET', 'POST'])
def download(file_id):
    try:
        file = File.get(id=file_id)
    except File.DoesNotExist:
        abort(404)

    # fetch the encrypted file contents from S3 and store in a memory
    bucket = get_bucket(app.config['AWSID'], app.config['AWSKEY'], app.config['AWSBUCKET'])
    key_obj = bucket.get_key(os.path.join(file.parent,file.filename))

    # read the contents of the key into an in-memory file
    enc_buffer = StringIO()
    key_obj.get_contents_to_file(enc_buffer)
    enc_buffer.seek(0)

    if not file.encrypted:
        return send_file(
            enc_buffer,
            file.get_mimetype(),
            as_attachment=True,
            attachment_filename=file.filename,
        )

    # new logic:
    if request.method == 'POST' and request.form.get('password'):
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
    else:
        flash("You must provide a password")
        return redirect(url_for('index'))

@app.route('/delete/<int:file_id>/')
def delete(file_id):
    try:
        file = File.get(id=file_id)
    except File.DoesNotExist:
        abort(404)
    bucket = get_bucket(app.config['AWSID'], app.config['AWSKEY'], app.config['AWSBUCKET'])
    key_obj = bucket.get_key(os.path.join(file.parent,file.filename))
    if key_obj:
        try:
            key_obj.delete()
        except:
            flash("There was an error deleting your file from S3!")
    if file.folder:        # S3 deletes all folder content, so we do the same.
        dq = File.delete().where(parent__istartswith=os.path.join(file.parent,file.filename))
        dq.execute()
    file.delete_instance()
    return redirect(url_for('index')+'?folder=%s'%session['folder'])

@app.route('/search/')
def search():
    if request.args.get('q',None):
        files = File.filter(filename__icontains=request.args.get('q')).order_by((File,'folder','DESC'),(File,'filename'))
        if files.count() == 0:
            files=None
        return render_template('search_results.html', files=files)
    else:
        return redirect(url_for('index')+'?folder=%s'%session['folder'])

if __name__ == '__main__':
    app.run()
