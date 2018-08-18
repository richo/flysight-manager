#!/usr/bin/env python
import io
import os
import toml
import base64

import flask
from flask import Flask, render_template, redirect, request, url_for, \
    session, send_file
import dropbox

import google_auth_oauthlib.flow

DROPBOX_KEY = os.getenv('DROPBOX_KEY')
DROPBOX_SECRET = os.getenv('DROPBOX_SECRET')

YOUTUBE_KEY = os.getenv('YOUTUBE_KEY')
YOUTUBE_SECRET = os.getenv('YOUTUBE_SECRET')

app = Flask(__name__)
app.secret_key = base64.b64encode(os.urandom(64))


def get_dropbox_flow():
    redirect_uri = url_for('/dropbox/finish', _external=True, _scheme='https')

    return dropbox.client.DropboxOAuth2Flow(DROPBOX_KEY, DROPBOX_SECRET,
                                            redirect_uri, session, "dropbox-auth-csrf-token")


def get_youtube_flow():
    # TODO we have a key and secret
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES) # noqa: F821
    flow.redirect_uri = flask.url_for('/youtube/finish', _external=True)
    return flow


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/youtube/authorise')
def youtube_authorize():
    flow = get_youtube_flow()
    authorization_url, state = flow.authorization_url(
        # This parameter enables offline access which gives your application
        # both an access and refresh token.
        access_type='offline',
        # This parameter enables incremental auth.
        include_granted_scopes='true')

    # Store the state in the session so that the callback can verify that
    # the authorization server response.
    flask.session['state'] = state

    return redirect(authorization_url)


@app.route('/youtube/finish')
def youtube_finish():
    # Specify the state when creating the flow in the callback so that it can
    # verify the authorization server response.
    state = flask.session['state']
    # TODO this is not how this works
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state) # noqa: F821
    flow.redirect_uri = flask.url_for('/youtube/finish', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    flask.session['youtube'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return flask.redirect(flask.url_for('/'))


@app.route('/dropbox/authorise')
def dropbox_authorize():
    url = get_dropbox_flow().start()
    return redirect(url)


@app.route('/dropbox/finish')
def dropbox_finish():
    access_token, _, _ = get_dropbox_flow().finish(request.args)
    session["dropbox"]["access_token"] = access_token


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
