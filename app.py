import flask
from flask import Response, request, send_file, Flask, render_template, session, redirect
import pandas as pd
pd.set_option('max_colwidth', 280)
from tweets import *
import os
from bokeh.embed import components

app = Flask(__name__, static_url_path='/static')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        visualize('download')
        button = request.form['submit']
        if button == 'download':
            namestable = pd.read_csv('names.csv')
            with open(key_file) as f:
                session['keys'] = json.load(f)
            download_all_tweets(namestable)
            return redirect('/')
        elif button == 'visualize tweet source':
            visualize('visualizetweetsource')
            namestable = pd.read_csv('names.csv')
            scounts = sourcecounts(namestable)
            script, div = components(scounts)
            return render_template('index.html', script=script, div=div)
        elif button == 'visualize number of tweets over time':
            visualize('visualizetweettime')
            namestable = pd.read_csv('names.csv')
            times = tweettimes(namestable)
            script, div = components(times)
            return render_template('index.html', script=script, div=div)
        elif button == 'visualize most retweeted tweets':
            visualize('visualizeretweets')
            namestable = pd.read_csv('names.csv')
            retweets = retweetcounts(namestable).to_html(index=False, escape=True)
            return render_template('index.html', tables=[retweets], titles=['na', 'Most Retweeted Tweets'])
        elif button == 'visualize tweet sentiment analysis':
            visualize('visualizesentiments')
            namestable = pd.read_csv('names.csv')
            sentiment = pd.read_table('vader_lexicon.txt')
            sentitweets = sentanalysis(namestable, sentiment).to_html(index=False, escape=True)
            return render_template('index.html', tables=[sentitweets], titles=['na', 'Sentiment Analysis'])
        elif button == 'update senate list':
            names = get_handles()
            pd.DataFrame(names, columns=["Senator", "Handle"]).to_csv('names.csv', index=False)
            session['handles'] = names
            visualize('names')
            return redirect('/')
    return render_template('index.html')

if __name__ == '__main__':
    app.debug=True
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run()
