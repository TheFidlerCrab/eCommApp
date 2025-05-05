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
    if 'loggedin' in session and session.get('userType') == 1:  # Use session.get to avoid KeyError
        action = request.form.get('action')
        account_request = db.session.execute(
            text("SELECT * FROM account_requests WHERE id = :id"),
            {"id": request_id}
        ).mappings().fetchone()

        if account_request:
            if action == 'approve':
                # Move account request into the users table
                db.session.execute(
                    text(
                        "INSERT INTO users (username, userPass, email, userType) "
                        "VALUES (:username, :userPass, :email, :userType)"
                    ),
                    {
                        "username": account_request['username'],
                        "userPass": account_request['userPass'],
                        "email": account_request['email'],
                        "userType": account_request['userType']  # Preserve user type (e.g., Customer or Vendor)
                    }
                )
                db.session.commit()  # Commit to generate the new user ID

                # If the account is a vendor, insert into the vendors table
                if account_request['userType'] == 2:
                    new_vendor_id = db.session.execute(
                        text("SELECT id FROM users WHERE username = :username"),
                        {"username": account_request['username']}
                    ).scalar()

                    db.session.execute(
                        text(
                            "INSERT INTO vendors (id, name, logo_path) "
                            "VALUES (:id, :name, :logo_path)"
                        ),
                        {
                            "id": new_vendor_id,
                            "name": account_request['store_name'],
                            "logo_path": account_request['logo_path']
                        }
                    )

                # Remove the account request after approval
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
    if 'loggedin' in session and session.get('userType') == 1:  # Use session.get to avoid KeyError
        # Fetch all pending account requests (both customers and vendors)
        pending_requests = db.session.execute(
            text("SELECT * FROM account_requests WHERE status = 'pending'")
        ).mappings().all()

        # Fetch already approved customers
        approved_customers = db.session.execute(
            text("SELECT id, username, email FROM users WHERE userType = 0")
        ).mappings().all()

        # Fetch already approved vendors
        approved_vendors = db.session.execute(
            text("SELECT id, username, email FROM users WHERE userType = 2")
        ).mappings().all()

        message = request.args.get('message', '')  # Retrieve message from query parameters
        return render_template(
            'adminDash.html',
            pending_requests=pending_requests,
            approved_customers=approved_customers,
            approved_vendors=approved_vendors,
            message=message
        )
    return redirect(url_for('login'))

@app.route('/remove_vendor/<int:vendor_id>', methods=['POST'])
def remove_vendor(vendor_id):
    if 'loggedin' in session and session.get('userType') == 1:  # Ensure admin is logged in
        # Remove vendor's products first to maintain database integrity
        db.session.execute(
            text("DELETE FROM products WHERE vendorId = :vendor_id"),
            {"vendor_id": vendor_id}
        )
        # Remove the vendor from the users table
        db.session.execute(
            text("DELETE FROM users WHERE id = :vendor_id AND userType = 2"),
            {"vendor_id": vendor_id}
        )
        db.session.commit()
        return redirect(url_for('admin_dashboard', message="Vendor removed successfully"))
    return redirect(url_for('login'))

@app.route('/remove_user/<int:user_id>', methods=['POST'])
def remove_user(user_id):
    if 'loggedin' in session and session.get('userType') == 1:  # Ensure admin is logged in
        # Remove the user from the users table
        db.session.execute(
            text("DELETE FROM users WHERE id = :user_id AND userType = 0"),
            {"user_id": user_id}
        )
        db.session.commit()
        return redirect(url_for('admin_dashboard', message="User removed successfully"))
    return redirect(url_for('login'))

@app.route('/user/dashboard')
def user_dashboard():
    if 'loggedin' in session and session.get('userType') == 0:  # Use session.get to avoid KeyError
        user_id = session['userId']  # Assuming user ID is stored in the session

        # Query to get user information
        user = db.session.execute(
            text("SELECT username AS name, email FROM users WHERE id = :id"),
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
    if 'loggedin' in session and session.get('userType') == 0:  # Use session.get to avoid KeyError
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
    if 'loggedin' in session and session.get('userType') == 2:  # Use session.get to avoid KeyError
        vendor_id = session['userId']  # Assuming vendor ID is stored in the session

        # Query to get vendor's store name
        vendor_store_name = db.session.execute(
            text("SELECT name FROM vendors WHERE id = :vendor_id"),
            {"vendor_id": vendor_id}
        ).scalar()

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

        # Query to get vendor's logo path
        vendor_logo = db.session.execute(
            text("SELECT logo_path FROM users WHERE id = :vendor_id"),
            {"vendor_id": vendor_id}
        ).scalar()

        return render_template(
            'vendorDash.html',
            vendor_name=vendor_store_name,  # Pass the store name instead of the username
            items=items,
            orders=orders,
            total_revenue=total_revenue or 0,
            vendor_logo=vendor_logo  # Pass the logo path to the template
        )

    return redirect(url_for('login'))

@app.route('/add_item', methods=['POST'])
def add_item():
    if 'loggedin' in session and session.get('userType') == 2:  # Use session.get to avoid KeyError
        vendor_id = session['userId']  # Assuming vendor ID is stored in the session

        # Verify that the vendor exists in the users table
        vendor_exists = db.session.execute(
            text("SELECT id FROM users WHERE id = :vendor_id AND userType = 2"),
            {"vendor_id": vendor_id}
        ).scalar()

        if not vendor_exists:
            return redirect(url_for('vendor_dashboard', message="Vendor does not exist"))

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

            return redirect(url_for('vendor_dashboard', message="Item added successfully"))

    return redirect(url_for('login'))

@app.route('/view_more_orders')
def view_more_orders():
    if 'loggedin' in session and session.get('userType') == 2:  # Use session.get to avoid KeyError
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

@app.route('/store', methods=['GET'])
def store():
    vendor_id = request.args.get('vendor_id')
    vendor_name = request.args.get('vendor_name')

    if vendor_id:
        # Query items by vendor ID
        items = db.session.execute(
            text("SELECT * FROM products WHERE vendorId = :vendor_id"),
            {"vendor_id": vendor_id}
        ).mappings().all()
    elif vendor_name:
        # Query items by vendor name
        items = db.session.execute(
            text("""
                SELECT p.* 
                FROM products p
                JOIN vendors v ON p.vendorId = v.id
                WHERE v.name LIKE :vendor_name
            """),
            {"vendor_name": f"%{vendor_name}%"}
        ).mappings().all()
    else:
        items = []

    return render_template('store.html', items=items)

@app.route('/featured')
def featured():
    return render_template('Featured.html')

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
            session['userType'] = user['userType']  # Ensure this is set correctly

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
        userType = request.form.get('userType')  # Dropdown to select user type
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate user type
        if userType == 'Customer':
            userType = 0  # Customer
        elif userType == 'Vendor':
            userType = 2  # Vendor
        else:
            return render_template('signup.html', error="Invalid user type selected")

        # Additional fields for vendors
        store_name = request.form.get('store_name') if userType == 2 else None
        logo_file = request.files.get('store_logo') if userType == 2 else None
        logo_path = None

        if userType == 2 and logo_file and allowed_file(logo_file.filename):
            vendor_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'logos')
            os.makedirs(vendor_upload_folder, exist_ok=True)  # Ensure the directory exists
            logo_filename = f"{username}_{logo_file.filename}"  # Create a unique filename
            logo_path = os.path.join(vendor_upload_folder, logo_filename)
            logo_file.save(logo_path)  # Save the file to the specified path
            logo_path = f"/static/uploads/logos/{logo_filename}"  # Save the relative path for database storage

        if password != confirm_password:
            return render_template('signup.html', error="Passwords do not match")

        # Insert account request into the database for admin approval
        db.session.execute(
            text("""
                INSERT INTO account_requests (username, userPass, email, userType, store_name, logo_path, status)
                VALUES (:username, :password, :email, :userType, :store_name, :logo_path, 'pending')
            """),
            {
                "username": username,
                "password": password,
                "email": email,
                "userType": userType,
                "store_name": store_name,
                "logo_path": logo_path
            }
        )
        db.session.commit()

        return redirect(url_for('login', message="Account request submitted for admin approval"))

    return render_template('signup.html')

@app.route('/')
def index():
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created before the app starts
    app.run(debug=True)

