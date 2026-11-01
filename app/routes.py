from functools import wraps
from itertools import product
import os
import cloudinary
import cloudinary.uploader
import uuid
from flask import ( Blueprint, render_template, request, redirect, url_for, session, flash, current_app )
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app import db
from app.models import User, Category, Product, CartItem, WishlistItem, Order, OrderItem

main = Blueprint("main", __name__)


cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("main.home"))
        return view(*args, **kwargs)
    return wrapped
@main.route("/")
def home():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)

    query = Product.query

    if q:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%")
            )
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    products = query.order_by(Product.created_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()

    wishlist_product_ids = set()

    if session.get("user_id"):
        wishlist_items = WishlistItem.query.filter_by(
            user_id=session["user_id"]
        ).all()

        wishlist_product_ids = {
            item.product_id for item in wishlist_items
        }

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        q=q,
        category_id=category_id,
        wishlist_product_ids=wishlist_product_ids
    )
@main.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", product=product)

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("main.register"))
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["name"] = user.name
            session["role"] = user.role
            flash("Welcome back!", "success")
            return redirect(url_for("main.admin_dashboard" if user.role == "admin" else "main.home"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@main.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.home"))

@main.route("/cart")
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=session["user_id"]).all()
    total = sum(i.product.price * i.quantity for i in items)
    return render_template("cart.html", items=items, total=total)

@main.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if product.stock < 1:
        flash("Product is out of stock.", "danger")
        return redirect(request.referrer or url_for("main.home"))
    item = CartItem.query.filter_by(user_id=session["user_id"], product_id=product.id).first()
    if item:
        if item.quantity < product.stock:
            item.quantity += 1
    else:
        db.session.add(CartItem(user_id=session["user_id"], product_id=product.id, quantity=1))
    db.session.commit()
    flash("Product added to cart.", "success")
    return redirect(request.referrer or url_for("main.home"))

@main.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart(item_id):

    item = CartItem.query.filter_by(
        id=item_id,
        user_id=session["user_id"]
    ).first_or_404()

    try:
        quantity = int(request.form.get("quantity", 1))
    except ValueError:
        flash("Please enter a valid quantity.", "danger")
        return redirect(url_for("main.cart"))

    if quantity < 1:
        flash("Quantity must be at least 1.", "warning")
        return redirect(url_for("main.cart"))

    if item.product.stock <= 0:
        flash(
            f"{item.product.name} is currently out of stock.",
            "danger"
        )

        db.session.delete(item)
        db.session.commit()

        return redirect(url_for("main.cart"))

    if quantity > item.product.stock:
        flash(
            f"Only {item.product.stock} units of "
            f"{item.product.name} are available.",
            "warning"
        )

        item.quantity = item.product.stock

    else:
        item.quantity = quantity

    db.session.commit()

    flash("Cart updated successfully.", "success")

    return redirect(url_for("main.cart"))

@main.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=session["user_id"]).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("main.cart"))

@main.route("/wishlist")
@login_required
def wishlist():
    items = WishlistItem.query.filter_by(user_id=session["user_id"]).all()
    return render_template("wishlist.html", items=items)

@main.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
@login_required
def toggle_wishlist(product_id):
    item = WishlistItem.query.filter_by(user_id=session["user_id"], product_id=product_id).first()
    if item:
        db.session.delete(item)
        flash("Removed from wishlist.", "success")
    else:
        db.session.add(WishlistItem(user_id=session["user_id"], product_id=product_id))
        flash("Added to wishlist.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("main.home"))

@main.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():

    items = CartItem.query.filter_by(
        user_id=session["user_id"]
    ).all()

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("main.home"))

    total = sum(
        i.product.price * i.quantity
        for i in items
    )

    if request.method == "POST":

        # Check stock
        for item in items:

            if item.quantity > item.product.stock:

                flash(
                    f"Insufficient stock for {item.product.name}.",
                    "danger"
                )

                return redirect(url_for("main.cart"))

        # Get checkout form data
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        pincode = request.form.get("pincode", "").strip()
        payment_method = request.form.get(
            "payment_method",
            "cod"
        )

        # Validate delivery information
        if not all([
            name,
            phone,
            email,
            address,
            city,
            state,
            pincode
        ]):

            flash(
                "Please complete all delivery details.",
                "warning"
            )

            return redirect(url_for("main.checkout"))

        # Create order
        order = Order(
            user_id=session["user_id"],
            total=total,
            status="Pending",
            name=name,
            phone=phone,
            email=email,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            payment_method=payment_method
        )

        db.session.add(order)

        # Generate order ID
        db.session.flush()

        # Create order items
        for item in items:

            item.product.stock -= item.quantity

            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item.product.id,
                    product_name=item.product.name,
                    price=item.product.price,
                    quantity=item.quantity
                )
            )

            db.session.delete(item)

        # Save order
        db.session.commit()

        flash(
            "Order placed successfully.",
            "success"
        )

        return redirect(
            url_for(
                "main.order_confirmation",
                order_id=order.id
            )
        )

    # GET request
    return render_template(
        "checkout.html",
        items=items,
        total=total
    )
@main.route("/orders")
@login_required
def orders():

    orders = Order.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Order.created_at.desc()
    ).all()

    return render_template(
        "orders.html",
        orders=orders
    )

@main.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):

    order = Order.query.filter_by(
        id=order_id,
        user_id=session["user_id"]
    ).first_or_404()

    return render_template(
        "order_detail.html",
        order=order
    )

@main.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):

    order = Order.query.filter_by(
        id=order_id,
        user_id=session["user_id"]
    ).first_or_404()

    # Only Pending or Confirmed orders can be cancelled
    if order.status not in ["Pending", "Confirmed"]:
        flash(
            "This order can no longer be cancelled.",
            "warning"
        )

        return redirect(
            url_for(
                "main.order_detail",
                order_id=order.id
            )
        )

    # Restore product stock
    for item in order.items:

        product = Product.query.get(item.product_id)

        if product:
            product.stock += item.quantity

    # Update order status
    order.status = "Cancelled"

    db.session.commit()

    flash(
        "Your order has been cancelled successfully.",
        "success"
    )

    return redirect(
        url_for(
            "main.order_detail",
            order_id=order.id
        )
    )
@main.route("/order/<int:order_id>/confirmation")
@login_required
def order_confirmation(order_id):
    order = Order.query.filter_by(
        id=order_id,
        user_id=session["user_id"]
    ).first_or_404()

    return render_template(
        "order_confirmation.html",
        order=order
    )

@main.route("/admin")
@admin_required
def admin_dashboard():
    products = Product.query.count()
    users = User.query.count()
    orders = Order.query.count()
    revenue = db.session.query(db.func.sum(Order.total)).scalar() or 0
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    return render_template("admin.html", products=products, users=users, orders=orders,
                           revenue=revenue, recent_orders=recent_orders)

@main.route("/admin/products")
@admin_required
def admin_products():
    products = Product.query.order_by(Product.id.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template("admin_products.html", products=products, categories=categories)

@main.route("/admin/products/add", methods=["POST"])
@admin_required
def admin_add_product():

    name = request.form["name"].strip()
    description = request.form["description"].strip()
    price = float(request.form["price"])
    stock = int(request.form["stock"])
    category_id = int(request.form["category_id"])

    image_url = request.form.get("image_url", "").strip()
    image_file = request.files.get("image_file")

    # ================= IMAGE UPLOAD =================
    if image_file and image_file.filename:


     allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}

     filename = secure_filename(image_file.filename)
     extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in allowed_extensions:
        flash(
            "Invalid image format. Use PNG, JPG, JPEG, GIF or WEBP.",
            "danger"
        )
        return redirect(url_for("main.admin_products"))

    upload_result = cloudinary.uploader.upload(
        image_file,
        folder="shopsphere/products"
    )

    image_url = upload_result["secure_url"]
    # =================================================

    product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        category_id=category_id,
        image_url=image_url
    )

    db.session.add(product)
    db.session.commit()

    flash("Product added successfully.", "success")

    return redirect(url_for("main.admin_products"))

@main.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def admin_delete_product(product_id):

    product = Product.query.get_or_404(product_id)

    # Check whether this product appears in any previous order
    existing_order_item = OrderItem.query.filter_by(
        product_id=product.id
    ).first()

    if existing_order_item:

        flash(
            "This product cannot be deleted because it is part of an existing order.",
            "warning"
        )

        return redirect(
            url_for("main.admin_products")
        )

    db.session.delete(product)

    db.session.commit()

    flash(
        "Product deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.admin_products")
    )

@main.route("/admin/products/edit/<int:product_id>", methods=["POST"])
@admin_required
def admin_edit_product(product_id):

    product = Product.query.get_or_404(product_id)

    # Update basic product details
    product.name = request.form.get("name", "").strip()
    product.description = request.form.get("description", "").strip()

    try:
        product.price = float(
            request.form.get("price", product.price)
        )

        product.stock = int(
            request.form.get("stock", product.stock)
        )

    except (ValueError, TypeError):

        flash(
            "Invalid price or stock value.",
            "danger"
        )

        return redirect(
            url_for("main.admin_products")
        )

    # Update category
    category_id = request.form.get("category_id")

    if category_id:
        product.category_id = int(category_id)

    # ================= IMAGE REPLACEMENT =================

    image_file = request.files.get("image")

    if image_file and image_file.filename:

        allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}

        filename = secure_filename(image_file.filename)
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in allowed_extensions:
        flash("Invalid image format.", "danger")
        return redirect(url_for("main.admin_products"))

    upload_result = cloudinary.uploader.upload(
        image_file,
        folder="shopsphere/products"
    )

    product.image_url = upload_result["secure_url"]

    # Save changes
    db.session.commit()

    flash(
        "Product updated successfully.",
        "success"
    )

    return redirect(
        url_for("main.admin_products")
    )

# ================= ADMIN ORDERS =================

@main.route("/admin/orders")
@admin_required
def admin_orders():

    orders = Order.query.order_by(
        Order.created_at.desc()
    ).all()

    return render_template(
        "admin_orders.html",
        orders=orders
    )


@main.route("/admin/orders/<int:order_id>")
@admin_required
def admin_order_detail(order_id):

    order = Order.query.get_or_404(order_id)

    return render_template(
        "admin_order_detail.html",
        order=order
    )


@main.route(
    "/admin/orders/<int:order_id>/status",
    methods=["POST"]
)
@admin_required
def admin_update_order(order_id):

    order = Order.query.get_or_404(order_id)

    allowed_statuses = {
        "Pending",
        "Confirmed",
        "Shipped",
        "Delivered",
        "Cancelled"
    }

    status = request.form.get("status")

    if status not in allowed_statuses:

        flash(
            "Invalid order status.",
            "danger"
        )

        return redirect(
            url_for("main.admin_orders")
        )

    order.status = status

    db.session.commit()

    flash(
        "Order status updated.",
        "success"
    )

    return redirect(
        url_for("main.admin_orders")
    )


@main.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin_users.html", users=users)


@main.cli.command("seed")
def seed():
    # Create default categories if missing
    for name in ["Electronics", "Fashion", "Shoes", "Home"]:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    db.session.commit()

    # Get the password from Render environment variables
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError(
            "ADMIN_PASSWORD is not set in Render environment variables"
        )

    # Create the admin or reset the existing admin password
    admin = User.query.filter_by(
        email="admin@shopsphere.com"
    ).first()

    if admin is None:
        admin = User(
            name="Admin",
            email="admin@shopsphere.com",
            role="admin"
        )
        db.session.add(admin)

    admin.role = "admin"
    admin.set_password(admin_password)
    db.session.commit()

    # Add sample products only if the database has no products
    if Product.query.count() == 0:
        cats = {c.name: c.id for c in Category.query.all()}
        products = [
            Product(
                name="Wireless Headphones",
                description="Comfortable Bluetooth headphones with clear sound.",
                price=2499, stock=20,
                category_id=cats["Electronics"],
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800"
            ),
            Product(
                name="Smart Watch",
                description="Fitness and notification smartwatch.",
                price=3999, stock=15,
                category_id=cats["Electronics"],
                image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800"
            ),
            Product(
                name="Classic Sneakers",
                description="Everyday lightweight sneakers.",
                price=2999, stock=25,
                category_id=cats["Shoes"],
                image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800"
            ),
            Product(
                name="Minimal Backpack",
                description="Modern backpack for college and work.",
                price=1799, stock=30,
                category_id=cats["Fashion"],
                image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800"
            ),
        ]
        db.session.add_all(products)
        db.session.commit()

    print("Admin account is ready: admin@shopsphere.com")