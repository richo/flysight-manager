#!/usr/bin/env python
import io
import os
import sys
import toml
import base64

from flask import Flask, render_template, redirect, request, url_for, \
    session, Response, send_file
import dropbox

import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from oauth2client.client import AccessTokenCredentials
import oauth2client.client
import google.oauth2.credentials

DROPBOX_KEY = os.getenv('DROPBOX_KEY')
DROPBOX_SECRET = os.getenv('DROPBOX_SECRET')

app = Flask(__name__)
app.secret_key = base64.b64encode(os.urandom(64))


def get_dropbox_flow():
    redirect_uri = url_for('/dropbox/finish', _external=True, _scheme='https')

    return dropbox.client.DropboxOAuth2Flow(DROPBOX_KEY, DROPBOX_SECRET,
            redirect_uri, session, "dropbox-auth-csrf-token")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/youtube/authorise')
def authorize():
    pass

@app.route('/youtube/finish')
def finish():
    pass


@app.route('/dropbox/authorise')
def authorize():
    url = get_flow().start()
    return redirect(url)


@app.route('/dropbox/finish')
def finish():
    access_token, _, _ = get_flow().finish(request.args)
    session["dropbox"]["access_token"]


@app.route('/config')
def config():
    return send_file(build_config(), mimetype="text/ini",
            as_attachment=True,
            attachment_filename="flysight-manager.ini")

def build_config():
    config = toml.load(open('flysight-manager.ini.example'))

    writer = io.BytesIO()
    config = toml.dumps(config)
    writer.write(bytes(config))

    writer.seek(0)
    return writer



if __name__ == "__main__":
    port = int(os.getenv("PORT") or 8000)
    app.run(host='0.0.0.0', port=port, debug=True)
