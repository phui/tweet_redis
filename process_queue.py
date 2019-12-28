#!/usr/bin/env python3
import os
import redis
import simplejson as json
from BotometerLite.core import BotometerLiteDetector



REDIS_HOST = os.environ['TWEET_REDIS_HOST']
REDIS_PORT = os.environ['TWEET_REDIS_RPORT']



load_json = json.loads



def main():
    r = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=0)

    pipeline = r.pipeline()
    pipeline.lrange('tweet_redis_history', 0, -1)
    pipeline.delete('tweet_redis_history')
    results = pipeline.execute()

    tweet_strings = results[0]
    tweet_objects = list()
    retweeted_uids = dict()
    for twt_str in tweet_strings:
        twt = load_json(twt_str)

        if 'retweeted_status' in twt:
            rusr = twt['retweeted_status']['user']

            rusr_desc = rusr['description']
            if rusr_desc is None:
                rusr_desc = ''
            rusr_desc = rusr_desc.lower()
            if ('auto dm' in rusr_desc) or \
                    ('autobase' in rusr_desc) or \
                    ('roleplay' in rusr_desc) or \
                    ('rolleplay' in rusr_desc) or \
                    ('automenfess' in rusr_desc):
                continue

            uid = twt['user']['id_str']
            ruid = rusr['id_str']
            if uid == ruid:
                continue

            tweet_objects.append(twt)
            tid = twt['id_str']
            retweeted_uids[int(tid)] = int(ruid)

    botometer = BotometerLiteDetector()
    bot_score_df = botometer.detect_on_tweet_objects(tweet_objects)
    bot_score_df['retweeted_uid'] = bot_score_df['tid'].map(retweeted_uids)

    echoed_by_bots = bot_score_df[
        bot_score_df.bot_score_lite > 0.5
    ].groupby('retweeted_uid').size()

    print(echoed_by_bots.sort_values(ascending=False))



if __name__ == '__main__': main()
