import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import session
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
                return redirect(url_for('admin_dashboard', message="Account approved."))
            elif action == 'reject':
                db.session.execute(
                    text("UPDATE account_requests SET status = 'rejected' WHERE id = :id"),
                    {"id": request_id}
                )
                db.session.commit()
                return redirect(url_for('admin_dashboard', message="Account rejected."))

    return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'loggedin' in session and session['userType'] == 1:  # Ensure admin is logged in
        account_requests = db.session.execute(
            text("SELECT * FROM account_requests WHERE status = 'pending'")
        ).mappings().all()
        return render_template('adminDash.html', account_requests=account_requests)
    return redirect(url_for('login'))

