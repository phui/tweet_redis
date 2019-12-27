FROM python:3.7-slim

WORKDIR /usr/src/app

COPY ./ /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .
RUN cp tweet_redis.db /var/log/tweet_redis.db

CMD ["python", "-m", "tweet_redis"]
