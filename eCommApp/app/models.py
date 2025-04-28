from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# User base model for Vendors, Customers, and Admins
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'vendor', 'customer', or 'admin'
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)

# Admin model
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    managed_requests = db.relationship('AccountRequest', backref='admin', lazy=True)

# Vendor model
class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    store_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    products = db.relationship('Product', backref='vendor', lazy=True)

# Product model
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='product', lazy=True)

# Account Request model for vendor account approvals
class AccountRequest(db.Model):
    __tablename__ = 'account_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submitted_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)  # Admin who handled the request
    decision_date = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], backref='account_requests')

# Order model
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'shipped', 'delivered'
    ordered_on = db.Column(db.DateTime, default=datetime.utcnow)

# Review model
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # e.g., 1 to 5 stars
    comment = db.Column(db.Text, nullable=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

# Customer Cart
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)