import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, flash
from flask_login import LoginManager, UserMixin, login_required, login_user
from flask_migrate import Migrate, upgrade
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)

with app.app_context():
    upgrade()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    minimum_quantity = db.Column(db.Integer, default=5, nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    category = db.relationship('Category', back_populates='products')


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

    products = db.relationship('Product', back_populates='category', lazy=True)


@app.cli.command("create-user")
def create_user():
    import click
    username = click.prompt("Digite o nome de usuário")
    password = click.prompt("Digite a senha", hide_input=True, confirmation_prompt=True)

    if db.session.query(User).filter_by(username=username).first():
        click.echo("Erro: Usuário já existe.")
        return

    new_user = User()
    new_user.username = username
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
    all_products = []
    try:
        stmt = db.select(Product).options(joinedload(Product.category)).limit(20)
        all_products = db.session.execute(stmt).scalars().all()
        print(f"Produtos encontrados: {len(all_products)}")
    except Exception as e:
        print(e)

    return render_template('pages/index.html', products=all_products)


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
    all_products = []
    categories_count = 0
    total_inventory_value = 0
    low_stock_count = 0

    try:
        stmt = db.select(Product).options(joinedload(Product.category)).limit(20)
        all_products = db.session.execute(stmt).scalars().all()

        categories_count = db.session.execute(db.select(func.count(Category.id))).scalar_one()

        inventory_stmt = db.select(func.sum(Product.price * Product.quantity))
        total_inventory_value = db.session.execute(inventory_stmt).scalar() or 0.0

        low_stock_stmt = db.select(func.count(Product.id)).where(Product.quantity < Product.minimum_quantity)
        low_stock_count = db.session.execute(low_stock_stmt).scalar_one()

    except Exception as e:
        print(e)

    return render_template('manage/dashboard.html',
                           products=all_products,
                           total_inventory_value=total_inventory_value,
                           estoque_baixo_count=low_stock_count,
                           categories_count=categories_count)


@app.route('/criar_produto', methods=['GET', 'POST'])
@login_required
def create_product():
    if request.method == 'POST':
        product = Product()
        product.name = request.form['productName']
        product.price = request.form['productPrice']
        product.description = request.form['productDescription']

        try:
            db.session.add(product)
            db.session.commit()
            flash('Produto criado com sucesso!', 'success')
            return redirect('/dashboard')
        except Exception as e:
            db.session.rollback()
            print(e)
            flash('Erro ao criar o produto!', 'danger')
            return redirect('/dashboard')
    return render_template('manage/create_product.html', produto=None)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
