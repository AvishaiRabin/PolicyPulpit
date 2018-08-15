import flask
from flask import Response, request, send_file, Flask, render_template, session, redirect
import pandas as pd
pd.set_option('max_colwidth', 280)
from tweets import *
import os

app = Flask(__name__, static_url_path='/static')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        visualize('download')
        button = request.form['submit']
        if button == 'download':
            with open(key_file) as f:
                session['keys'] = json.load(f)
            download_tweets("realdonaldtrump")
            return render_template('index.html')
        elif button == 'visualize':
            visualize('visualize')
            load_tweets("realdonaldtrump")
            return redirect('/')
    return render_template('index.html')

if __name__ == '__main__':
    app.debug=True
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run()
