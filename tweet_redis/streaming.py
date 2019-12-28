#!/usr/bin/env python3
import os
import sys
import time
import redis
import sqlite3
import twython
import logging
import requests
import simplejson as json
from tweet_redis.database import FIELDS, DBPATH, config_read


logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s [streaming]',
    level=logging.INFO
)


REDIS_HOST = os.environ['TWEET_REDIS_HOST']
REDIS_PORT = os.environ['TWEET_REDIS_RPORT']


class RedisStreamer(twython.TwythonStreamer):
    def __init__(self, channel, history, *args, **kwargs):
        self._redis = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=0)
        self._channel= channel
        self._history = history
        super().__init__(*args, **kwargs)

    def on_success(self, data):
        message = json.dumps(data)
        self._redis.lpush(self._history, message)

    def on_error(self, status_code, data):
        logging.error("Error, code {}".format(status_code))
        if status_code == 420:
            logging.error("This is a rate limit error, sleeping for one minute.")
            time.sleep(60)
            logging.error("Waking up from sleep.")


def main():
    # fetch query along with other settings
    db = sqlite3.connect(DBPATH)
    cur = db.cursor()
    config = config_read(cur)
    cur.close()
    db.close()

    consumer_api_key = config['consumer_api_key']
    consumer_api_key_secret = config['consumer_api_key_secret']
    access_token = config['access_token']
    access_token_secret = config['access_token_secret']

    streamer = RedisStreamer(
        'tweet_redis_channel', 'tweet_redis_history',
        consumer_api_key, consumer_api_key_secret,
        access_token, access_token_secret
    )
    del consumer_api_key, consumer_api_key_secret, access_token, access_token_secret

    # parse queries from db
    query = dict()

    track_str = config.get('track', '')
    if len(track_str) > 0:
        track = list(set([term.strip() for term in track_str.split(',')]))
        if len(track) > 0:
            query['track'] = track

    follow_str = config.get('follow', '')
    if len(follow_str) > 0:
        follow = list(set([term.strip() for term in follow_str.split(',')]))
        if len(follow) > 0:
            query['follow'] = follow

    locations_str = config.get('locations', '')
    if len(locations_str) > 0:
        locations = [float(co.strip()) for co in locations_str.split(',')]
        if len(locations) > 0:
            query['locations'] = locations

    print(query, file=sys.stderr)

    while True:
        try:
            # start streaming
            if len(query) > 0:
                # there is something to track
                streamer.statuses.filter(tweet_mode='extended', **query)
            else:
                # nothing to track, do random 1% sample
                logging.info("no parameter given, randomly sampling")
                streamer.statuses.sample()
        except requests.exceptions.ChunkedEncodingError:
            logging.exception("Incomplete Read")
            time.sleep(30)



if __name__ == '__main__':
    main()
