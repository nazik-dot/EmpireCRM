from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///service.db'
app.config['SQLALCHEMY_TRACK_NOTIFICATIONS'] = False

login_manager = LoginManager(app)
login_manager.login_message = 'Please, login to access the service.'
login_manager.login_view = 'login'

db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(150))
    address = db.Column(db.String(200))
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float)
    stage = db.Column(db.String(50))
    probability = db.Column(db.Integer)
    expected_close_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50))
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50))
    payment_date = db.Column(db.DateTime)

    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now)

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if User.query.filter_by(username=username).first():
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('main'))
    return render_template('login.html')

@app.route('/main')
@login_required
def main():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('main.html')

@app.route('/clients', methods=['GET', 'POST', 'PUT', 'DELETE'])
def clients():
    if request.method == 'POST':
        name = request.form['name']
        company = request.form['company']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        status = request.form['status']
        client = Client(name=name, company=company, email=email, phone=phone, address=address, status=status, user_id=current_user.id)
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('main'))
    elif request.method == 'PUT':
        data = request.get_json()
        client = Client.query.filter_by(id=data['id'], user_id=current_user.id).first()
        if client:
            client.name = data['name']
            client.company = data['company']
            client.email = data['email']
            client.phone = data['phone']
            client.address = data['address']
            client.status = data['status']
            db.session.commit()
            return '', 204
        return '', 404
    elif request.method == 'DELETE':
        data = request.get_json()
        client = Client.query.filter_by(id=data['id'], user_id=current_user.id).first()
        if client:
            db.session.delete(client)
            db.session.commit()
            return '', 204
        return '', 404
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.created_at.desc()).all()
    return render_template('clients.html', clients=clients)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)