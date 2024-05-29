from flask import render_template, flash, redirect, url_for, request, jsonify, abort
from app import app, db
from models import User, Item, Order, CartItem, Category
from forms import (
    LoginForm,
    RegistrationForm,
    AddItemForm,
    EditItemForm,
    AddCategoryForm,
)
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from decorators import admin_required
from notification_manager import NotificationManager
import stripe
import json

stripe.api_key = app.config['STRIPE_SECRET_KEY']


@app.context_processor
def inject_stripe_key():
    return dict(stripe_public_key=app.config['STRIPE_PUBLIC_KEY'])


@app.route('/')
@app.route('/index')
def index():
    category_id = request.args.get('category_id', type=int)
    categories = Category.query.all()

    if category_id:
        items = Item.query.filter_by(category_id=category_id).all()
    else:
        items = Item.query.all()

    return render_template(
        'index.html',
        title='Home',
        items=items,
        categories=categories,
        selected_category=category_id,
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
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
        flash('Congratulations, you are now a registered user!', 'success')
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
        cart_item = CartItem(user_id=current_user.id, item_id=item_id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    flash(f'Added {item.name} to your cart.', 'success')
    return redirect(url_for('index'))


@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    action = request.form.get('action')
    cart_item = CartItem.query.filter_by(
        id=item_id, user_id=current_user.id
    ).first_or_404()

    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
    elif action == 'decrease' and cart_item.quantity == 1:
        db.session.delete(cart_item)

    db.session.commit()
    return redirect(url_for('cart'))


@app.route('/delete_cart_item/<int:item_id>', methods=['POST'])
@login_required
def delete_cart_item(item_id):
    cart_item = CartItem.query.filter_by(
        id=item_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart'))


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
            status='Pending',
        )
        order.serialize_items(
            cart_items
        )  # Serialize items before adding the order to the session
        db.session.add(order)
        db.session.commit()

        # Clear the cart
        for cart_item in cart_items:
            db.session.delete(cart_item)
        db.session.commit()

        # Send email notification
        notification_manager = NotificationManager()
        subject = "Order Confirmation"
        html_body = render_template(
            'email/order_confirmation.html',
            user=current_user,
            order=order,
            items=json.loads(order.serialized_items),
        )
        notification_manager.send_email(
            subject, html_body, current_user.email, html=True
        )

        return render_template(
            'order_confirmation.html',
            title='Order Confirmation',
            order=order,
            payment_intent=payment_intent,
        )
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('index'))


@app.route('/order_history')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    order_details = []

    for order in orders:
        serialized_items = json.loads(order.serialized_items)
        order_details.append({'order': order, 'order_items': serialized_items})

    return render_template(
        'order_history.html', title='Order History', order_details=order_details
    )


@app.route('/order/<int:order_id>')
@login_required
def order_details(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    serialized_items = json.loads(order.serialized_items)  # Parse the serialized items
    return render_template(
        'order_details.html', title='Order Details', order=order, items=serialized_items
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
            stock=form.stock.data,
            weight=form.weight.data,
            category_id=form.category.data,
        )
        db.session.add(item)
        db.session.commit()
        flash('Item has been added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_item.html', title='Add Item', form=form)


@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_details(product_id):
    product = Item.query.get_or_404(product_id)
    form = EditItemForm(obj=product)

    if form.validate_on_submit():
        if current_user.is_authenticated and current_user.is_admin:
            product.name = form.name.data
            product.description = form.description.data
            product.price = form.price.data
            product.image = form.image.data
            product.stock = form.stock.data
            product.weight = form.weight.data
            product.category_id = form.category.data

            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('product_details', product_id=product_id))
        else:
            flash('You do not have permission to edit this product.', 'danger')

    return render_template(
        'product_details.html', title='Product Details', product=product, form=form
    )


@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Item.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product has been deleted successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/manage_categories', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_categories():
    form = AddCategoryForm()
    categories = Category.query.all()

    if form.validate_on_submit():
        category = Category(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('manage_categories'))

    return render_template(
        'manage_categories.html',
        title='Manage Categories',
        form=form,
        categories=categories,
    )


@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    # Ensure no items are associated with this category before deleting
    if category.items:
        flash('Cannot delete category with associated items!', 'danger')
        return redirect(url_for('manage_categories'))

    db.session.delete(category)
    db.session.commit()
    flash('Category has been deleted successfully!', 'success')
    return redirect(url_for('manage_categories'))


"""TODO:
4. Improved UI/UX.
"""
