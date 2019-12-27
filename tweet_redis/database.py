FIELDS = [
    'track', 'follow', 'locations',
    'consumer_api_key', 'consumer_api_secret',
    'access_token', 'access_token_secret'
]
DBPATH = '/var/log/tweet_redis.db'


def config_read(cur):
    '''
        read sqllite config table and return content
    '''
    return { k:v for k, v in cur.execute('SELECT * FROM config;').fetchall() }


def config_save(cur, data):
    '''
        acquire thread lock to write to sqllite
        and then read back the resultant config
    '''
    cur.execute("BEGIN")
    try:
        cur.execute('DELETE FROM config;')
        cur.executemany(
            'INSERT INTO config(name, val) VALUES (?,?)',
            list(data.items()))
    except Exception as e:
        #TODO: think about what exception to catch
        #TODO: error logging
        cur.execute('ROLLBACK')
        raise e
