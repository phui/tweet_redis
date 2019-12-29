#!/usr/bin/env python3
import os
import redis
import pandas as pd
import simplejson as json
from BotometerLite.core import BotometerLiteDetector



REDIS_HOST = os.environ['TWEET_REDIS_HOST']
REDIS_PORT = os.environ['TWEET_REDIS_RPORT']



load_json = json.loads



def main():
    botometer = BotometerLiteDetector()
    r = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=0)

    num_elements = r.llen('tweet_redis_history')
    batch_size = 10000
    end = None
    echoed_by_bots = pd.Series()
    retweeted_tids = dict()
    retweeted_tags = dict()
    for start in range(0, num_elements-batch_size, batch_size):
        end = start+batch_size
        print(start, end)
        tweet_strings = r.lrange('tweet_redis_history', start, end)
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
                        ('menfess' in rusr_desc):
                    continue

                uid = twt['user']['id_str']
                ruid = rusr['id_str']
                if uid == ruid:
                    continue

                tweet_objects.append(twt)
                tid = twt['id_str']
                retweeted_tids[int(tid)] = retweeted_tids.get(int(tid), 0)+1
                retweeted_uids[int(tid)] = int(ruid)
                for tag in twt['entities']['hashtags']:
                    tag_txt = tag['text'].lower()
                    retweeted_tags[tag_txt] = retweeted_tags.get(tag_txt, 0)+1
        bot_score_df = botometer.detect_on_tweet_objects(tweet_objects)
        bot_score_df['retweeted_uid'] = bot_score_df['tid'].map(retweeted_uids)

        echoed_by_bots = echoed_by_bots.add(
            bot_score_df[
                bot_score_df.bot_score_lite > 0.5
            ].groupby('retweeted_uid').size(),
            fill_value=0
        )

    print(echoed_by_bots.sort_values(ascending=False).iloc[:50])
    print('tid')
    print(pd.Series(retweeted_tids).sort_values(ascending=False).iloc[:50])
    print('tag')
    print(pd.Series(retweeted_tags).sort_values(ascending=False).iloc[:50])
    #r.ltrim('tweet_redis_history', 0, end) 



if __name__ == '__main__': main()
