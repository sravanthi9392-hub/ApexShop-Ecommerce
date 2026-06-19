import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Product, Cart, Order, OrderItem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-production-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Local file upload directory configuration matrix
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions validator checklist
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'webp', 'gif'}

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access Denied: Administrative privileges required.', 'danger')
            return redirect(url_for('home'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.context_processor
def inject_cart_count():
    count = 0
    if current_user.is_authenticated:
        count = sum(item.quantity for item in Cart.query.filter_by(user_id=current_user.id).all())
    return dict(cart_count=count)

# --- AUTHENTICATION ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email address already registered.', 'danger')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(name=name, email=email, password_hash=hashed_pw, role='user')

        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

# --- CUSTOMER PLATFORM ROUTES ---

@app.route('/')
def home():
    featured_products = Product.query.order_by(Product.id.desc()).limit(4).all()
    return render_template('home.html', products=featured_products)

@app.route('/products')
def products():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    page = request.args.get('page', 1, type=int)

    query = Product.query
    if search:
        query = query.filter(Product.name.like(f"%{search}%") | Product.description.like(f"%{search}%"))
    if category:
        query = query.filter_by(category=category)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    pagination = query.paginate(page=page, per_page=8, error_out=False)
    return render_template('products.html', products=pagination.items, pagination=pagination, search=search, category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter(Product.category == product.category, Product.id != product.id).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    tax = subtotal * 0.05
    grand_total = subtotal + tax
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal, tax=tax, grand_total=grand_total)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    qty = int(request.form.get('quantity', 1))

    if product.stock_quantity < qty:
        flash(f'Insufficient item stock. Only {product.stock_quantity} remaining.', 'warning')
        return redirect(request.referrer or url_for('products'))

    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if cart_item:
        if product.stock_quantity < (cart_item.quantity + qty):
            flash('Cannot add item capacity beyond current physical stock.', 'warning')
            return redirect(url_for('cart'))
        cart_item.quantity += qty
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product.id, quantity=qty)
        db.session.add(cart_item)

    db.session.commit()
    flash(f'{product.name} added to cart.', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/update/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.user_id != current_user.id:
        return redirect(url_for('cart'))
    
    qty = int(request.form.get('quantity'))
    if qty <= 0:
        db.session.delete(cart_item)
    else:
        if cart_item.product.stock_quantity < qty:
            flash('Selected quantity exceeds stock levels.', 'danger')
            return redirect(url_for('cart'))
        cart_item.quantity = qty
    
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('products'))

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    grand_total = subtotal + (subtotal * 0.05)

    if request.method == 'POST':
        for item in cart_items:
            if item.product.stock_quantity < item.quantity:
                flash(f'Stock changed for {item.product.name}. Adjust quantity.', 'danger')
                return redirect(url_for('cart'))

        order = Order(
            user_id=current_user.id,
            total_amount=grand_total,
            full_name=request.form.get('full_name'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            pincode=request.form.get('pincode')
        )
        db.session.add(order)
        db.session.flush()

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            item.product.stock_quantity -= item.quantity
            db.session.add(order_item)
            db.session.delete(item)

        db.session.commit()
        flash('Order completed successfully!', 'success')
        return redirect(url_for('orders'))

    return render_template('checkout.html', cart_items=cart_items, grand_total=grand_total)

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/dashboard')
@login_required
def dashboard():
    user_orders = Order.query.filter_by(user_id=current_user.id).all()
    total_orders = len(user_orders)
    pending = len([o for o in user_orders if o.order_status == 'Pending'])
    delivered = len([o for o in user_orders if o.order_status == 'Delivered'])
    cart_items_count = sum(item.quantity for item in Cart.query.filter_by(user_id=current_user.id).all())
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).limit(5).all()

    return render_template('dashboard.html', total_orders=total_orders, pending=pending, 
                           delivered=delivered, cart_items_count=cart_items_count, recent_orders=recent_orders)

# --- ADMINISTRATIVE SYSTEM ROUTES ---

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_products = Product.query.count()
    orders = Order.query.all()
    total_orders = len(orders)
    revenue = sum(o.total_amount for o in orders if o.order_status != 'Cancelled')

    return render_template('admin_dashboard.html', total_users=total_users, 
                           total_products=total_products, total_orders=total_orders, revenue=revenue)

@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_products():
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        price = float(request.form.get('price'))
        description = request.form.get('description')
        stock = int(request.form.get('stock'))
        image_url = request.form.get('image_url', '').strip()

        # Handle local laptop file streaming upload
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"prod_{name.replace(' ', '_').lower()}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                image_url = f"/static/uploads/{unique_filename}"

        if not image_url:
            image_url = "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500"

        prod = Product(name=name, category=category, price=price, description=description, image_url=image_url, stock_quantity=stock)
        db.session.add(prod)
        db.session.commit()
        flash('Product registered successfully.', 'success')
        return redirect(url_for('manage_products'))

    products = Product.query.all()
    return render_template('manage_products.html', products=products)

@app.route('/admin/products/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    product.name = request.form.get('name')
    product.category = request.form.get('category')
    product.price = float(request.form.get('price'))
    product.description = request.form.get('description')
    product.stock_quantity = int(request.form.get('stock'))
    
    # Priority-Smart check: Did the admin upload a physical file from their laptop?
    file_uploaded = False
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"prod_{id}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            product.image_url = f"/static/uploads/{unique_filename}"
            file_uploaded = True

    # Priority-Smart check: If NO file was uploaded, check if a text URL link was submitted
    if not file_uploaded:
        new_url = request.form.get('image_url', '').strip()
        if new_url:
            product.image_url = new_url
            
    db.session.commit()
    flash('Product modified successfully.', 'success')
    return redirect(url_for('manage_products'))

@app.route('/admin/products/delete/<int:id>')
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted from index.', 'info')
    return redirect(url_for('manage_products'))

@app.route('/admin/orders', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_orders():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        status = request.form.get('status')
        order = Order.query.get(order_id)
        if order:
            order.order_status = status
            db.session.commit()
            flash(f'Order #{order_id} modified to {status}.', 'success')
        return redirect(url_for('manage_orders'))

    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('manage_orders.html', orders=orders)

# --- REST APIs ENDPOINTS ---

@app.route('/api/products', methods=['GET', 'POST'])
def api_products():
    if request.method == 'GET':
        products = Product.query.all()
        return jsonify([{
            'id': p.id, 'name': p.name, 'category': p.category, 
            'price': p.price, 'stock_quantity': p.stock_quantity, 'image_url': p.image_url
        } for p in products])
    
    if request.method == 'POST':
        data = request.json or {}
        new_p = Product(
            name=data.get('name'), description=data.get('description'), category=data.get('category'),
            price=float(data.get('price', 0)), stock_quantity=int(data.get('stock_quantity', 0)), image_url=data.get('image_url')
        )
        db.session.add(new_p)
        db.session.commit()
        return jsonify({'message': 'Product generated', 'id': new_p.id}), 201

@app.route('/api/products/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_product_detail(id):
    product = Product.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'description': product.description, 'stock_quantity': product.stock_quantity, 'category': product.category, 'image_url': product.image_url})
    
    if request.method == 'PUT':
        data = request.json or {}
        product.name = data.get('name', product.name)
        product.price = float(data.get('price', product.price))
        product.description = data.get('description', product.description)
        product.stock_quantity = int(data.get('stock_quantity', product.stock_quantity))
        product.category = data.get('category', product.category)
        product.image_url = data.get('image_url', product.image_url)
        db.session.commit()
        return jsonify({'message': 'Product update executed successfully'})
    
    if request.method == 'DELETE':
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product wiped out successfully'})

@app.route('/api/orders', methods=['GET', 'POST'])
def api_orders():
    if request.method == 'GET':
        orders = Order.query.all()
        return jsonify([{
            'id': o.id, 'user_id': o.user_id, 'total_amount': o.total_amount, 'order_status': o.order_status, 'order_date': o.order_date.isoformat()
        } for o in orders])
    
    if request.method == 'POST':
        data = request.json or {}
        new_order = Order(
            user_id=data.get('user_id'), total_amount=float(data.get('total_amount', 0)),
            full_name=data.get('full_name'), phone=data.get('phone'), address=data.get('address'),
            city=data.get('city'), state=data.get('state'), pincode=data.get('pincode')
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({'message': 'Order deployed successfully', 'id': new_order.id}), 201

@app.route('/api/orders/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_order_detail(id):
    order = Order.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({'id': order.id, 'user_id': order.user_id, 'total_amount': order.total_amount, 'status': order.order_status, 'date': order.order_date.isoformat()})
    
    if request.method == 'PUT':
        data = request.json or {}
        order.order_status = data.get('order_status', order.order_status)
        db.session.commit()
        return jsonify({'message': 'Order payload modification executed.'})
    
    if request.method == 'DELETE':
        db.session.delete(order)
        db.session.commit()
        return jsonify({'message': 'Order removed.'})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# ==========================================================================
# RENDER DEPLOYMENT DATABASE INITIALIZER
# ==========================================================================
# Executed globally outside the run block so Gunicorn creates missing tables on Render
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
