from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from models import db, UserAccount, Quote, PolicyTransaction, Policy
import pandas as pd
import joblib
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from config import SECRET_KEY
from risk_model import train_model, NEW_MODEL_PATH
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config.from_object('config')
db.init_app(app)

UPLOAD_FOLDER = 'datasets'
EXISTING_MODEL_PATH = "risk_model.pkl"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        primary_contact = request.form['primary_contact']
        region = request.form['region']

        new_user = UserAccount(
            UserName=username,
            PasswordHash=password,
            UserRole='Customer',
            PrimaryContact=primary_contact,
            Region=region
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login', success=1))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = UserAccount.query.filter_by(UserName=username).first()

        if user and check_password_hash(user.PasswordHash, password):
            session['user_id'] = user.UserID
            session['username'] = user.UserName
            session['role'] = user.UserRole
            if user.UserRole == 'Admin':
                return redirect(url_for('admin_homepage'))
            return redirect(url_for('customer_homepage'))
        error = "Login failed!"

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/customer_homepage')
def customer_homepage():
    if 'user_id' not in session or session.get('role') != 'Customer':
        return redirect(url_for('login'))
    user_policies = Policy.query.filter_by(
        CustomerID=session.get('user_id')).all()
    return render_template('customer_homepage.html', policies=user_policies)


@app.route('/admin_homepage', methods=['GET', 'POST'])
def admin_homepage():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    message = ""
    accuracy = None

    if request.method == 'POST':
        if 'file' in request.files and 'test_size' in request.form:
            uploaded_file = request.files['file']
            test_size = float(request.form['test_size'])

            if not uploaded_file or not uploaded_file.filename.endswith('.csv'):
                message = "Please upload a valid CSV file."
            else:
                file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
                uploaded_file.save(file_path)

                result = train_model(file_path, test_size)
                if result['success']:
                    accuracy = result['accuracy']
                    message = result['message']
                else:
                    message = result['message']

        elif 'use_model' in request.form:
            os.replace(NEW_MODEL_PATH, EXISTING_MODEL_PATH)
            message = "The new model is in use!"

        elif 'discard_model' in request.form:
            if os.path.exists(NEW_MODEL_PATH):
                os.remove(NEW_MODEL_PATH)
            message = "The new model is discarded!"

    return render_template('admin_homepage.html', message=message, accuracy=accuracy)


@app.route('/insurance_form', methods=['GET'])
def insurance_form():
    return render_template('insurance_form.html')


@app.route('/generate_quote/<int:user_id>', methods=['POST'])
def generate_quote(user_id):
    user = UserAccount.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    age = int(request.form['age'])
    height = float(request.form['height'])
    weight = float(request.form['weight'])
    smoking = int(request.form.get('smoking', 0))
    chronic_disease = int(request.form.get('chronic_disease', 0))
    policy_type = request.form['policy_type']
    subproduct = request.form['subproduct']
    bmi = weight / (height / 100) ** 2

    try:
        risk_model = joblib.load('risk_model.pkl')
        input_data = pd.DataFrame([[age, bmi, smoking, chronic_disease]],
                                  columns=['age', 'bmi', 'smoking', 'chronic_disease'])

        risk_score = risk_model.predict_proba(input_data)[:, 1][0]
        base_premium = 500 + (risk_score * 1000)

        price_multiplier = 1.0

        if policy_type == "Health Insurance":
            price_multiplier = 1.5 if subproduct == "Premium" else 2.0 if subproduct == "Gold" else 1.2
            base_premium += 50 if age > 50 else 20
        elif policy_type == "Car Insurance":
            price_multiplier = 1.3 if subproduct == "Premium" else 1.6 if subproduct == "Gold" else 1.0
            base_premium += 30 if age < 25 else 10
        elif policy_type == "Home Insurance":
            price_multiplier = 1.4 if subproduct == "Premium" else 1.8 if subproduct == "Gold" else 1.1

        premium_quoted = base_premium * price_multiplier

        new_quote = Quote(
            CustomerID=user_id,
            PolicyType=policy_type,
            SubProduct=subproduct,
            RiskScore=round(risk_score, 2),
            PremiumQuoted=round(premium_quoted, 2),
            Status="Issued"
        )

        db.session.add(new_quote)
        db.session.commit()

        return render_template('quote_generated.html', quote=new_quote)

    except Exception as e:
        return jsonify({'error': f"Error loading model: {str(e)}"}), 500


@app.route('/accept_quote/<int:quote_id>', methods=['POST'])
def accept_quote(quote_id):
    quote = Quote.query.get(quote_id)
    if not quote:
        return jsonify({'message': 'Quote not found'}), 404

    quote.Status = 'Accepted'

    new_policy = Policy(
        CustomerID=quote.CustomerID,
        QuoteID=quote.QuoteID,
        PolicyType=quote.PolicyType,
        SubProduct=quote.SubProduct,
        PremiumAmount=quote.PremiumQuoted,
        Status='Inactive'
    )

    db.session.add(new_policy)
    db.session.commit()

    return render_template('quote_accepted.html', policy=new_policy)


@app.route('/reject_quote/<int:quote_id>', methods=['POST'])
def reject_quote(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    quote = Quote.query.get(quote_id)
    if not quote:
        return jsonify({'message': 'Quote not found'}), 404

    quote.Status = 'Rejected'

    db.session.commit()

    return render_template('quote_rejected.html')


@app.route('/make_payment/<int:policy_id>', methods=['POST'])
def make_payment(policy_id):
    policy = Policy.query.get(policy_id)
    if not policy:
        return jsonify({'message': 'Policy not found'}), 404

    if not policy.QuoteID:
        return jsonify({'message': 'No Quote associated with this policy'}), 400

    policy.Status = 'Active'
    policy.EffectiveDate = datetime.now(timezone.utc)
    policy.UpdatedAt = datetime.now(timezone.utc)

    new_transaction = PolicyTransaction(
        PolicyID=policy.PolicyID,
        CustomerID=policy.CustomerID,
        QuoteID=policy.QuoteID,
        PaymentAmount=policy.PremiumAmount,
        TransactionStatus='Completed'
    )

    db.session.add(new_transaction)
    db.session.commit()

    return render_template('payment_success.html', policy=policy)


if __name__ == '__main__':
    app.run(debug=True)
