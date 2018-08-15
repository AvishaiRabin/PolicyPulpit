import pandas as pd
pd.set_option('max_colwidth', 280)
import tweepy
import json
from flask import Response, request, send_file, Flask, render_template, session
key_file = 'keys.json'
from pathlib import Path
from tweepy import TweepError
import logging
import datetime

# Downloads all tweets in the last week from a user and stores it in a json file under the name of their username
def download_tweets(username):
    today = datetime.date.today()
    today = datetime.datetime(today.year, today.month, today.day)
    week_ago = today - datetime.timedelta(days=7)
    try: # the try-except block is code given to me in Berkeley's datascience 100 class.  I changed it a little to fit the needs of my program
        keys = session['keys']
        auth = tweepy.OAuthHandler(keys["consumer_key"], keys["consumer_secret"])
        auth.set_access_token(keys["access_token"], keys["access_token_secret"])
        api = tweepy.API(auth)
    except TweepError as e:
        logging.warning("There was a Tweepy error. Double check your API keys and try again.")
        logging.warning(e)
    tweets = tweepy.Cursor(api.user_timeline, # this part is actually not the time-consuming one
                           id=username,
                           since_id=week_ago,
                           tweet_mode='extended').items()
    new_tweets = []
    for tweet in tweets:
        if tweet.created_at > week_ago:
            new_tweets.append(tweet._json)
        else: # because we download tweets chronologically we can break after a week
            break
    save_path = username + '.json'
    with open(save_path, "w") as f:
        json.dump(new_tweets, f)
    session[username] = save_path

def load_tweets(username):
    save_path = username + '.json'
    with open(save_path, "r") as f:
        session[username] = json.load(f)

def visualize(keyword):
    indicators_to_show = ['visualize', 'download']
    for i in indicators_to_show:
        session[i] = False
    session[keyword] = True
