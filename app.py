from datetime import datetime

from flask import Flask, render_template

app = Flask(__name__)


@app.context_processor
def inject_now():
    return dict(now=datetime.now())


@app.route('/')
def index():
    return render_template('pages/index.html')


@app.route('/login')
def login():
    return render_template('pages/login.html')


@app.route('/dashboard')
def dashboard():
    return render_template('manage/dashboard.html', total_estoque=0.00, estoque_baixo_count=0, categorias_count=0)


if __name__ == '__main__':
    app.run(debug=True)
