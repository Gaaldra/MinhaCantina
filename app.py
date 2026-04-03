import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, flash
from flask_login import LoginManager, UserMixin, login_required, login_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@app.cli.command("create-user")
def create_user():
    import click
    username = click.prompt("Digite o nome de usuário")
    password = click.prompt("Digite a senha", hide_input=True, confirmation_prompt=True)

    if db.session.query(User).filter_by(username=username).first():
        click.echo("Erro: Usuário já existe.")
        return

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    click.echo(f"Usuário '{username}' criado com sucesso!")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_now():
    return dict(now=datetime.now())


@app.route('/')
def index():
    return render_template('pages/index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['usernameMC']
        password = request.form['passwordMC']

        user = db.session.query(User).filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect('dashboard')
        else:
            flash('Erro na autenticação, tente novamente', 'danger')

    return render_template('pages/login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('manage/dashboard.html', total_estoque=0.00, estoque_baixo_count=0, categorias_count=0)


if __name__ == '__main__':
    app.run(debug=True)
