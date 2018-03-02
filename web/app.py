#!/usr/bin/env python
import io
import os
import sys
import base64

if sys.version_info.major == 2:
    import ConfigParser as configparser
else:
    import configparser

from flask import Flask, render_template, redirect, request, url_for, \
    session, Response, send_file
import dropbox

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


@app.route('/dropbox/authorise')
def authorize():
    url = get_flow().start()
    return redirect(url)


@app.route('/dropbox/finish')
def finish():
    access_token, _, _ = get_flow().finish(request.args)

    return send_file(build_config(access_token), mimetype="text/ini",
            as_attachment=True,
            attachment_filename="flysight-manager.ini")

def build_config(token):
    defaults = {
            'mountpoint': 'flysight',
            'storage_backend': 'dropbox',
            'dropbox_token': token,
    }

    cfg = configparser.RawConfigParser()
    cfg.add_section('flysight-manager')
    for k, v in defaults.items():
        cfg.set('flysight-manager', k, v)
    writer = io.BytesIO()
    cfg.write(writer)

    writer.seek(0)
    return writer



if __name__ == "__main__":
    port = int(os.getenv("PORT") or 8000)
    app.run(host='0.0.0.0', port=port, debug=True)
