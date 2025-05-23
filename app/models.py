from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    userPass = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    userType = db.Column(db.Integer, nullable=False)  # 0: User, 1: Admin, 2: Vendor
    logo_path = db.Column(db.String(255))

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)  # Use id from users table
    name = db.Column(db.String(100), nullable=False)  # Store name of the vendor
    logo_path = db.Column(db.String(255), nullable=True)  # Path to vendor's logo
    products = db.relationship('Product', backref='vendor', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    vendorId = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

class AccountRequest(db.Model):
    __tablename__ = 'account_requests'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    userPass = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    userType = db.Column(db.Integer, nullable=False)  # 0 for Customer, 2 for Vendor
    store_name = db.Column(db.String(100), nullable=True)  # Only for vendors
    logo_path = db.Column(db.String(255), nullable=True)  # Only for vendors
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    orderDate = db.Column(db.DateTime, nullable=False)
    totalAmount = db.Column(db.Numeric(10, 2), nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    orderId = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    productId = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    productId = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    productId = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)