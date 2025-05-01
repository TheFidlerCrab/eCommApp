import datetime
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import session
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text
from models import db, User, Admin, Vendor, Product, AccountRequest, Order, Review, CartItem  # Import models

app = Flask(__name__, static_folder='static')
app.secret_key = 'pingus'
conn_str = 'mysql://root:TheFiddyCrab8918@localhost/ecommercedb'
engine = create_engine(conn_str,echo=True)
conn = engine.connect()

app.config['SQLALCHEMY_DATABASE_URI'] = conn_str
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)  # Link SQLAlchemy to the Flask app

UPLOAD_FOLDER = 'c:/Users/round/OneDrive/Desktop/180 final/eCommApp/app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/update_request/<int:request_id>', methods=['POST'])
def update_request(request_id):
    if 'loggedin' in session and session['userType'] == 1:  # Ensure admin is logged in
        action = request.form.get('action')
        account_request = db.session.execute(
            text("SELECT * FROM account_requests WHERE id = :id"),
            {"id": request_id}
        ).mappings().fetchone()

        if account_request:
            if action == 'approve':
                db.session.execute(
                    text(
                        "INSERT INTO users (username, userPass, firstName, lastName, email, userPhone, ssnNum, userType) "
                        "VALUES (:username, :userPass, :firstName, :lastName, :email, :userPhone, :ssnNum, 0)"
                    ),
                    {
                        "username": account_request['username'],
                        "userPass": account_request['userPass'],
                        "firstName": account_request['firstName'],
                        "lastName": account_request['lastName'],
                        "email": account_request['email'],
                        "userPhone": account_request['userPhone'],
                        "ssnNum": account_request['ssnNum']
                    }
                )
                db.session.execute(
                    text("DELETE FROM account_requests WHERE id = :id"),
                    {"id": request_id}
                )
                db.session.commit()
                return redirect(url_for('admin_dashboard', message="Account approved"))
            elif action == 'reject':
                db.session.execute(
                    text("UPDATE account_requests SET status = 'rejected' WHERE id = :id"),
                    {"id": request_id}
                )
                db.session.commit()
                return redirect(url_for('admin_dashboard', message="Account rejected"))

    return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'loggedin' in session and session['userType'] == 1:  # Ensure admin is logged in
        account_requests = db.session.execute(
            text("SELECT * FROM account_requests WHERE status = 'pending'")
        ).mappings().all()
        message = request.args.get('message', '')  # Retrieve message from query parameters
        return render_template('adminDash.html', account_requests=account_requests, message=message)
    return redirect(url_for('login'))

@app.route('/remove_vendor/<int:vendor_id>', methods=['POST'])
def remove_vendor(vendor_id):
    if 'loggedin' in session and session['userType'] == 1:  # Ensure admin is logged in
        db.session.execute(
            text("DELETE FROM vendors WHERE id = :id"),
            {"id": vendor_id}
        )
        db.session.commit()
        return redirect(url_for('admin_dashboard', message="Vendor removed"))
    return redirect(url_for('login'))

@app.route('/remove_user/<int:user_id>', methods=['POST'])
def remove_user(user_id):
    if 'loggedin' in session and session['userType'] == 1:  # Ensure admin is logged in
        db.session.execute(
            text("DELETE FROM users WHERE id = :id"),
            {"id": user_id}
        )
        db.session.commit()
        return redirect(url_for('admin_dashboard', message="User removed"))
    return redirect(url_for('login'))

@app.route('/user/dashboard')
def user_dashboard():
    if 'loggedin' in session and session['userType'] == 0:  # Ensure user is logged in
        user_id = session['userId']  # Assuming user ID is stored in the session

        # Query to get user information
        user = db.session.execute(
            text("SELECT firstName AS name, email FROM users WHERE id = :id"),
            {"id": user_id}
        ).mappings().fetchone()

        # Query to get order history
        orders = db.session.execute(
            text("SELECT id, orderDate AS date, totalAmount AS total FROM orders WHERE userId = :id"),
            {"id": user_id}
        ).mappings().all()

        # Query to get vendors the user has purchased from
        vendors = db.session.execute(
            text("""
                SELECT DISTINCT v.name 
                FROM vendors v
                JOIN products p ON v.id = p.vendorId
                JOIN order_items oi ON p.id = oi.productId
                JOIN orders o ON oi.orderId = o.id
                WHERE o.userId = :id
            """),
            {"id": user_id}
        ).mappings().all()

        return render_template('userDash.html', user=user, orders=orders, vendors=vendors)

    return redirect(url_for('login'))

@app.route('/order/<int:order_id>/items')
def view_order_items(order_id):
    if 'loggedin' in session and session['userType'] == 0:  # Ensure user is logged in
        user_id = session['userId']  # Assuming user ID is stored in the session

        # Query to get items in the order, including image URL
        order_items = db.session.execute(
            text("""
                SELECT p.name AS product_name, oi.quantity, oi.price, p.image_url 
                FROM order_items oi
                JOIN products p ON oi.productId = p.id
                WHERE oi.orderId = :order_id AND EXISTS (
                    SELECT 1 FROM orders o WHERE o.id = :order_id AND o.userId = :user_id
                )
            """),
            {"order_id": order_id, "user_id": user_id}
        ).mappings().all()

        return render_template('orderItems.html', order_items=order_items, order_id=order_id)

    return redirect(url_for('login'))

@app.route('/vendor/dashboard')
def vendor_dashboard():
    if 'loggedin' in session and session['userType'] == 2:  # Ensure vendor is logged in
        vendor_id = session['userId']  # Assuming vendor ID is stored in the session

        # Query to get vendor's items
        items = db.session.execute(
            text("SELECT id, name, price, stock FROM products WHERE vendorId = :vendor_id"),
            {"vendor_id": vendor_id}
        ).mappings().all()

        # Query to get vendor's orders
        orders = db.session.execute(
            text("""
                SELECT o.id, o.orderDate AS date, o.totalAmount AS total 
                FROM orders o
                JOIN order_items oi ON o.id = oi.orderId
                JOIN products p ON oi.productId = p.id
                WHERE p.vendorId = :vendor_id
                GROUP BY o.id
            """),
            {"vendor_id": vendor_id}
        ).mappings().all()

        # Query to calculate total revenue
        total_revenue = db.session.execute(
            text("""
                SELECT SUM(oi.price * oi.quantity) AS revenue
                FROM order_items oi
                JOIN products p ON oi.productId = p.id
                WHERE p.vendorId = :vendor_id
            """),
            {"vendor_id": vendor_id}
        ).scalar()

        return render_template('vendorDash.html', vendor_name=session['username'], items=items, orders=orders, total_revenue=total_revenue or 0)

    return redirect(url_for('login'))

@app.route('/add_item', methods=['POST'])
def add_item():
    if 'loggedin' in session and session['userType'] == 2:  # Ensure vendor is logged in
        vendor_id = session['userId']  # Assuming vendor ID is stored in the session
        name = request.form['name']
        price = request.form['price']
        stock = request.form['stock']
        image = request.files['image']

        if image and allowed_file(image.filename):
            vendor_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'vendor_{vendor_id}')
            if not os.path.exists(vendor_upload_folder):
                os.makedirs(vendor_upload_folder)  # Create vendor-specific folder if it doesn't exist

            filename = image.filename
            image_path = os.path.join(vendor_upload_folder, filename)
            image.save(image_path)

            # Insert new item into the database
            db.session.execute(
                text("INSERT INTO products (name, price, stock, vendorId, image_url) VALUES (:name, :price, :stock, :vendor_id, :image_url)"),
                {"name": name, "price": price, "stock": stock, "vendor_id": vendor_id, "image_url": f'/static/uploads/vendor_{vendor_id}/{filename}'}
            )
            db.session.commit()

            return redirect(url_for('vendor_dashboard'))

    return redirect(url_for('login'))

@app.route('/view_more_orders')
def view_more_orders():
    if 'loggedin' in session and session['userType'] == 2:  # Ensure vendor is logged in
        vendor_id = session['userId']  # Assuming vendor ID is stored in the session

        # Query to get all vendor's orders
        orders = db.session.execute(
            text("""
                SELECT o.id, o.orderDate AS date, o.totalAmount AS total 
                FROM orders o
                JOIN order_items oi ON o.id = oi.orderId
                JOIN products p ON oi.productId = p.id
                WHERE p.vendorId = :vendor_id
                GROUP BY o.id
            """),
            {"vendor_id": vendor_id}
        ).mappings().all()

        return render_template('vendorOrders.html', orders=orders)

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query to validate user credentials
        user = db.session.execute(
            text("SELECT * FROM users WHERE username = :username AND userPass = :password"),
            {"username": username, "password": password}
        ).mappings().fetchone()

        if user:
            session['loggedin'] = True
            session['userId'] = user['id']
            session['username'] = user['username']
            session['userType'] = user['userType']  # 0: User, 1: Admin, 2: Vendor

            # Redirect based on user type
            if user['userType'] == 0:
                return redirect(url_for('user_dashboard'))
            elif user['userType'] == 1:
                return redirect(url_for('admin_dashboard'))
            elif user['userType'] == 2:
                return redirect(url_for('vendor_dashboard'))

        return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        store_name = request.form.get('store_name')
        store_logo = request.files.get('store_logo')

        if password != confirm_password:
            return render_template('signup.html', error="Passwords do not match")

        # Insert account request into the database
        db.session.execute(
            text("""
                INSERT INTO account_requests (username, userPass, email, role, store_name, status)
                VALUES (:username, :password, :email, :role, :store_name, 'pending')
            """),
            {
                "username": username,
                "password": password,
                "email": email,
                "role": role,
                "store_name": store_name
            }
        )
        db.session.commit()

        return redirect(url_for('login', message="Account request submitted for approval"))

    return render_template('signup.html')

@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created before the app starts
    app.run(debug=True)

