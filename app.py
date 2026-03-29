from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

@app.context_processor
def inject_now():
    return dict(now=datetime.now())

@app.route('/')
def index():
    return render_template('public/index.html')

@app.route('/login')
def login():
    return render_template('public/login.html')

if __name__ == '__main__':
    app.run(debug=True)
