# Tweet-Redis

Tweet-Redis is a Python package that streams twitter into a redis channel.

`Redis` supports the publish/subscribe protocol, which allows multiple consumer applications down the pipeline of data collection pipeline.

In my work, I have found this a common pattern.
For example, I am collecting tweets that contains the word "cat".
First, I would like to dump hourly backup of all the collected tweets to a data server.
But I also want to have a dashboard provding some info-graphics about the cat discussion on Twitter during the last hour.
Maybe I also want to index some information and put them in a SQL database, which is more accessible for analysis than the raw dumps.
And then a colleague overhead me talking about cute cat pictures I collected, and suggest we download all the pictures to build the largest cat picture collection on Earth.

Instead of having a super long pipeline

A picture here.

It's much more flexible to have a flatten pipeline

Another picture here. 

You get the idea ;)

# Architecture

Tweet-Redis consists of two Docker containers, one as `redis` server and another streaming from Twitter.
The `redis` container is built from the official `redis` docker image directly.

The streaming container runs two processes simutaneously.
The first process is, of course, the `twython` streamer publishing to the `redis` server.
The streamer process reads queries from a `sqlite3` database file.
This `sqlite3` database has only one table, namely `config`.
The second process, serving a `Flask` form, fills the table and restarts the streamer process when a new form is submitted.

# Usage

Assuming you have `Docker` and `docker-compose` both installed (they are different!) properly in your system, you can launch Tweet-Redis via

    docker-compose up

Simple as that.
Now you can go to the `Flask` form at `http://0.0.0.0:5000` with your browser and fill in the queries and keys.
Once you hit submit, the streamer process will starts to pulbish the collected tweets to the `redis` server.

From now on, each time you update the queries using the `Flask` form, the streamer process will restart immediately.
