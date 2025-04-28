from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort  # Added abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_wtf.file import FileField, FileAllowed
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    products = db.relationship('Product', backref='creator', lazy=True)  

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def load_initial_products():
    if Product.query.count() == 0:
        try:
            with open('initial_products.json') as f:
                products = json.load(f)
                for p in products:
                    product = Product(
                        name=p['name'],
                        price=p['price'],
                        description=p['description'],
                        category=p['category'],
                        image_url=p.get('image_url'),
                        stock=p.get('stock', 0),
                        user_id=1  
                    )
                    db.session.add(product)
                db.session.commit()
        except Exception as e:
            print(f"Error loading products: {str(e)}")
            db.session.rollback()

with app.app_context():
    db.create_all()
    
    if User.query.count() == 0:
        admin = User(
            username='admin',
            email='admin@example.com',
            password='admin123'  
        )
        db.session.add(admin)
        db.session.commit()
    
    if Product.query.count() == 0:
        try:
            with open('initial_products.json') as f:
                products = json.load(f)
                for p in products:
                    product = Product(
                        name=p['name'],
                        price=p['price'],
                        description=p['description'],
                        category=p['category'],
                        image_url=p.get('image_url'),
                        stock=p.get('stock', 0),
                        user_id=1  
                    )
                    db.session.add(product)
                db.session.commit()
        except Exception as e:
            print(f"Error loading products: {str(e)}")
            db.session.rollback()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    description = TextAreaField('Description')
    category = SelectField('Category', choices=[
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('home', 'Home Goods')
    ])
    stock = IntegerField('Stock', validators=[DataRequired()])
    image = FileField('Product Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Add Product')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=20)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])
    submit = SubmitField('Register')

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        try:
            image_url = None
            if form.image.data:
                file = form.image.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_url = url_for('static', filename=f'uploads/{filename}')

            product = Product(
                name=form.name.data,
                price=form.price.data,
                description=form.description.data,
                category=form.category.data,
                stock=form.stock.data,
                image_url=image_url,
                user_id=current_user.id 
            )
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
    return render_template('add_product.html', form=form)

@app.route('/api/products')
def api_products():
    try:
        category = request.args.get('category')
        query = Product.query
        
        if category and category.lower() != 'all':
            query = query.filter_by(category=category)
        
        products = query.all()
        
        products_data = []
        for p in products:
            image_url = p.image_url
            if p.image_url and not p.image_url.startswith(('http://', 'https://', '/')):
                image_url = url_for('static', filename=f'uploads/{p.image_url}', _external=True)
            
            products_data.append({
                'id': p.id,
                'name': p.name,
                'price': float(p.price),
                'description': p.description,  
                'image_url': image_url,
                'category': p.category,
                'stock': p.stock,
                'delete_url': url_for('delete_product', product_id=p.id)
            })
        
        return jsonify(products_data)
    
    except Exception as e:
        app.logger.error(f"Error in api_products: {str(e)}")
        return jsonify({'error': 'Failed to load products', 'details': str(e)}), 500

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if product.user_id != current_user.id:
        abort(403, description="You can only delete your own products")
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully', 'success')
        return redirect(url_for('products'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
        return redirect(url_for('products'))
        
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)