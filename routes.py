from flask import render_template, flash, redirect, url_for, request, jsonify, abort
from app import app, db
from models import User, Item, Order, CartItem
from forms import LoginForm, RegistrationForm, AddItemForm
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from decorators import admin_required
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
        username = form.username.data
        email = form.email.data
        user = User(username=username, email=email)
        user.set_password(form.password.data)
        if email == app.config['ADMIN_EMAIL']:
            user.is_admin = True
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
@login_required
def add_to_cart(item_id):
    item = Item.query.get_or_404(item_id)
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id, item_id=item_id
    ).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, item_id=item_id)
        db.session.add(cart_item)
    db.session.commit()
    flash(f'Added {item.name} to your cart.')
    return redirect(url_for('index'))


@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_amount = sum(item.item.price * item.quantity for item in cart_items)
    return render_template(
        'cart.html',
        title='Shopping Cart',
        cart_items=cart_items,
        total_amount=total_amount,
    )


@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    if cart_item.user_id != current_user.id:
        abort(403)
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from your cart.')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        try:
            cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
            line_items = []

            for cart_item in cart_items:
                line_items.append(
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': cart_item.item.name,
                            },
                            'unit_amount': int(
                                cart_item.item.price * 100
                            ),  # Stripe expects amount in cents
                        },
                        'quantity': cart_item.quantity,
                    }
                )

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=url_for('order_confirmation', _external=True)
                + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('cart', _external=True),
            )
            return jsonify({'id': session.id})
        except Exception as e:
            return jsonify(error=str(e)), 403

    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_amount = sum(item.item.price * item.quantity for item in cart_items)
    return render_template(
        'checkout.html',
        title='Checkout',
        cart_items=cart_items,
        total_amount=total_amount,
    )


@app.route('/order_confirmation', methods=['GET'])
@login_required
def order_confirmation():
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect(url_for('index'))

    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        payment_intent = stripe.PaymentIntent.retrieve(checkout_session.payment_intent)
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        total_amount = sum(item.item.price * item.quantity for item in cart_items)

        # Create a new order
        order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            items=";".join([str(item.item_id) for item in cart_items]),
        )
        db.session.add(order)
        db.session.commit()

        # Clear the cart
        for cart_item in cart_items:
            db.session.delete(cart_item)
        db.session.commit()

        return render_template(
            'order_confirmation.html',
            title='Order Confirmation',
            order=order,
            payment_intent=payment_intent,
        )
    except Exception as e:
        flash(str(e))
        return redirect(url_for('index'))


@app.route('/order_history')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    order_details = []

    for order in orders:
        items = []
        for item_id in order.items.split(';'):
            item = Item.query.get(item_id)
            if item:
                items.append(item)
        order_details.append({'order': order, 'order_items': items})

    return render_template(
        'order_history.html', title='Order History', order_details=order_details
    )


@app.route('/add_item', methods=['GET', 'POST'])
@login_required
@admin_required
def add_item():
    form = AddItemForm()
    if form.validate_on_submit():
        item = Item(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image=form.image.data,
        )
        db.session.add(item)
        db.session.commit()
        flash('Item has been added successfully!')
        return redirect(url_for('index'))
    return render_template('add_item.html', title='Add Item', form=form)
