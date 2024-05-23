from flask import render_template, flash, redirect, url_for, request, jsonify
from app import app, db
from models import User, Item, Order
from forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
import stripe

stripe.api_key = app.config['STRIPE_SECRET_KEY']


@app.context_processor
def inject_stripe_key():
    return dict(stripe_public_key=app.config['STRIPE_PUBLIC_KEY'])


@app.route('/')
@app.route('/index')
def index():
    items = Item.query.all()
    return render_template('index.html', title='Home', items=items)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/cart')
@login_required
def cart():
    # TODO: Implement the logic to display the shopping cart
    return render_template('cart.html', title='Shopping Cart')


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        try:
            # TODO: Get a way to get the cart total amount
            total_amount = 1000  # This should be calculated based on cart contents

            # TODO: Add way of selection payment method types
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'Total Order',
                            },
                            'unit_amount': total_amount,
                        },
                        'quantity': 1,
                    }
                ],
                mode='payment',
                success_url=url_for('order_confirmation', _external=True),
                cancel_url=url_for('cart', _external=True),
            )
            return jsonify({'id': session.id})
        except Exception as e:
            return jsonify(error=str(e)), 403

    return render_template('checkout.html', title='Checkout')


@app.route('/order_confirmation')
@login_required
def order_confirmation():
    # TODO: Implement the logic to display the order confirmation
    return render_template('order_confirmation.html', title='Order Confirmation')
