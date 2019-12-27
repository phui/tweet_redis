#!/usr/bin/env python3
import os
import sys
import sqlite3
import multiprocessing
from datetime import timedelta
from flask import g, Flask, render_template, flash, request, jsonify, session
from flask_wtf import FlaskForm
from wtforms import TextField, TextAreaField, validators, StringField, SubmitField
from wtforms.csrf.session import SessionCSRF
try:
    import simplejson as json
except ImportError:
    import json


from tweet_redis.database import FIELDS, DBPATH, config_read, config_save
import tweet_redis.streaming as tstream
stream_func = tstream.main
stream_process = None
def restart_stream():
    global stream_process
    try:
        if stream_process is not None:
            stream_process.terminate()
    except Exception as e:
        pass
    finally:
        stream_process = multiprocessing.Process(target=stream_func)
        stream_process.start()



SECRET_KEY = os.urandom(16)
app = Flask(__name__,
    template_folder="./templates",
    static_folder="./templates/assets"
)
app.config.from_object(__name__)
app.config['WTF_CSRF_SECRET_KEY'] = SECRET_KEY



def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DBPATH)
        db.isolation_level = None
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



class SQLiteForm(FlaskForm):
    track = TextField('Track:')
    follow = TextField('Follow:')
    locations = TextField('Locations:')
    consumer_api_key = TextField('Consumer API Key:',
        validators=[
            validators.DataRequired(
                message="Consumer API Key is required for streaming."),
            validators.Length(min=25, max=25,
                message="Consumer API Keys are 25 characters long.")
        ])
    consumer_api_key_secret = TextField('Consumer API Key Secret:',
        validators=[
            validators.DataRequired(
                message="Consumer API Key Secret is required for streaming."),
            validators.Length(min=50, max=50,
                message="Consumer API Key Secrets are 50 characters long.")
        ])
    access_token = TextField('Access Token:',
        validators=[
            validators.DataRequired(
                message="Access Token is required for streaming."),
            validators.Length(min=50, max=50,
                message="Access Tokens are 50 characters long.")
        ])
    access_token_secret = TextField('Access Token Secret:',
        validators=[
            validators.DataRequired(
                message="Access Token Secret is required for streaming."),
            validators.Length(min=45, max=45,
                message="Access Token Secrets are 45 characters long.")
        ])

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = app.config['SECRET_KEY']
        csrf_time_limit = timedelta(minutes=10)

        @property
        def csrf_context(self):
            return session



@app.route("/", methods=('GET', 'POST'))
def index():
    db = get_db()
    cur = db.cursor()
    form = SQLiteForm(request.form)

    if request.method == "GET":
        config = config_read(cur)
        print(config, file=sys.stdout)

        form.track.data = config.get('track', '')
        form.follow.data = config.get('follow', '')
        form.locations.data = config.get('locations', '')
        form.consumer_api_key.data = config.get('consumer_key_api', '')
        form.consumer_api_key_secret.data = config.get('consumer_api_key_secret', '')
        form.access_token.data = config.get('access_token', '')
        form.access_token_secret.data = config.get('access_token_secret', '')
    elif request.method == "POST":
        data = {
            'track'    : request.form['track'],
            'follow'   : request.form['follow'],
            'locations': request.form['locations'],
            'consumer_api_key' : request.form['consumer_api_key'],
            'consumer_api_key_secret' : request.form['consumer_api_key_secret'],
            'access_token' : request.form['access_token'],
            'access_token_secret' : request.form['access_token_secret']
        }
        print(data, file=sys.stdout)
        if form.validate_on_submit():
            config_save(cur, data)
            db.commit()
            restart_stream()
        else:
            print('invalid', file=sys.stdout)
            print(form.errors, file=sys.stdout)

    return render_template('/index.html', form=form)



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=int(os.environ['TWEET_REDIS_FPORT']))
