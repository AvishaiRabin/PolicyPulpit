import pandas as pd
import numpy as np
pd.set_option('max_colwidth', 280)
import tweepy
import json
from flask import Response, request, send_file, Flask, render_template, session
key_file = 'keys.json'
from pathlib import Path
from tweepy import TweepError
import logging
import datetime
import selenium
import re
from bokeh.plotting import figure
from dateutil import parser

def get_handles():
    html = "https://www.socialseer.com/resources/us-senator-twitter-accounts/"
    from selenium import webdriver
    senate = webdriver.Firefox()
    senate.get(html)
    names = []
    senaterange = range(2, 102)
    for i in senaterange:
        path1 = "/html/body/div/div/div/div/article/div/table[1]/tbody/tr[%s]/td[3]/a" % (i)
        element1 = senate.find_element_by_xpath(path1)
        name1 = element1.text
        path2 = "/html/body/div/div/div/div/article/div/table[1]/tbody/tr[%s]/td[2]" % (i)
        element2 = senate.find_element_by_xpath(path2)
        name2 = element2.text
        names.append([name2, name1])
    return names

def download_all_tweets(namestable):
    names = namestable['Handle']
    for name in names:
        download_tweets(name)

# Downloads all tweets in the last week from a user and stores it in a json file under the name of their username
def download_tweets(username):
    print(username)
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

def sourcecounts(namestable):
    handles = namestable['Handle']
    tweets = []
    for i in handles:
        tweets.append(load_tweets(i))
    fulltweets = []
    for tweetlist in tweets:
        for tweet in tweetlist:
            fulltweets.append(re.findall('>.+?<', tweet['source'])[0][1:-1])
    fulltweets = pd.Series(fulltweets).value_counts().to_frame()
    fulltweets = fulltweets.rename(columns={0:'value counts'})
    categories =  [i for i in fulltweets.index]
    colors = ['red', 'orange', 'gold', 'green', 'blue', 'indigo', 'violet']
    p = figure(x_range=categories, plot_height=400, plot_width=1250, title="Tweet Source Counts",
    toolbar_location='above')
    p.vbar(x=categories, top=[i for i in fulltweets['value counts']], width=0.9, color=colors)
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    return p

def tweettimes(namestable):
    handles = namestable['Handle']
    tweets = []
    for i in handles:
        tweets.append(load_tweets(i))
    fulltweets = []
    for tweetlist in tweets:
        for tweet in tweetlist:
            fulltweets.append(parser.parse(tweet['created_at']).replace(minute=0, second=0))
    fulltweets = pd.Series(fulltweets).value_counts().to_frame()
    fulltweets = fulltweets.rename(columns={0:'Time of Tweet'})
    fulltweets = fulltweets.sort_index()
    categories = [i for i in fulltweets.index]
    p = figure(
        plot_height=400, plot_width=1250, title="Tweet activity of all U.S. senators in the last week",
        toolbar_location='above', x_axis_type='datetime'
        )
    p.line(x=categories, y=[i for i in fulltweets['Time of Tweet']], line_width=0.9)
    p.xgrid.grid_line_color=None
    return p

def retweetcounts(namestable):
    handles = namestable['Handle']
    tweets = []
    for i in handles:
        tweets.append(load_tweets(i))
    fulltweets = []
    for tweetlist in tweets:
        for tweet in tweetlist:
            fulltweets.append([tweet['user']['name'], tweet['full_text'], tweet['retweet_count']])
    fulltweets = pd.DataFrame(fulltweets, columns=['Name', 'Text', 'Retweet Count'])
    fulltweets = fulltweets.sort_values(by=['Retweet Count'])
    return fulltweets.tail(10).iloc[::-1]

def sentanalysis(namestable, lexicon):
    lexicon.loc[-1] = lexicon.columns
    lexicon.index = lexicon.index+1
    lexicon = lexicon.sort_index()
    lexicon.index = lexicon['$:']
    lexicon = lexicon.rename(columns = {'-1.5' : 'polarity'})
    lexicon = lexicon[['polarity']]
    lexicon.index = lexicon.index.rename('token')
    lexicon['polarity'] = [float(i) for i in lexicon['polarity']]
    handles = namestable['Handle']
    tweets = []
    for i in handles:
        tweets.append(load_tweets(i))
    fulltweets = []
    for tweetlist in tweets:
        for tweet in tweetlist:
            fulltweets.append([tweet['user']['name'], tweet['full_text']])
    fulltweets = pd.DataFrame(fulltweets, columns=['Name', 'Text'])
    fulltweets['Text'] = fulltweets['Text'].str.lower().str.replace('[^\s\w]', ' ')
    fulltweets['Text'] = [eval(i, lexicon) for i in fulltweets['Text']]
    toptweets = most_positive_tweets(fulltweets)
    categories = [i for i in toptweets.index]
    p = figure(x_range=categories, plot_height=400, plot_width=1250, title="Tweet Source Counts",
    toolbar_location='above')
    p.vbar(x=categories, top=[i for i in fulltweets['Text']], width=0.9)
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    return p


def most_positive_tweets(table):
    return table.groupby('Name').mean().sort_values('Text').iloc[::-1]


def load_tweets(username):
    save_path = username + '.json'
    with open(save_path, "r") as f:
        return json.load(f)

def visualize(keyword):
    indicators_to_show = ['visualizetweetsource', 'download', 'names', 'visualizetweettime', 'visualizeretweets']
    for i in indicators_to_show:
        session[i] = False
    session[keyword] = True

def eval(tweet, lexicon):
    tweet = tweet.split()
    tweet = pd.DataFrame(tweet, columns=['text'])
    tweet = tweet.merge(lexicon, left_on='text', right_index=True, how='left').fillna(0)
    return np.sum(tweet['polarity'])
