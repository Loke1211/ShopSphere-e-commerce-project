
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

        # Seed database only when explicitly enabled
        if os.getenv("AUTO_SEED") == "true":
            from app.models import Category, Product, User

            categories = ["Electronics", "Fashion", "Shoes", "Home"]

            for category_name in categories:
                if not Category.query.filter_by(name=category_name).first():
                    db.session.add(Category(name=category_name))

            db.session.commit()

            admin_email = "admin@shopsphere.com"
            admin = User.query.filter_by(email=admin_email).first()

            if not admin:
                admin_password = os.getenv("ADMIN_PASSWORD")

                if not admin_password:
                    raise RuntimeError("ADMIN_PASSWORD is not configured.")

                admin = User(
                    name="Admin",
                    email=admin_email,
                    role="admin"
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()

            if Product.query.count() == 0:
                category_ids = {
                    category.name: category.id
                    for category in Category.query.all()
                }

                products = [
                    Product(
                        name="Wireless Headphones",
                        description="Comfortable Bluetooth headphones with clear sound.",
                        price=2499,
                        stock=20,
                        category_id=category_ids["Electronics"],
                        image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800"
                    ),
                    Product(
                        name="Smart Watch",
                        description="Fitness and notification smartwatch.",
                        price=3999,
                        stock=15,
                        category_id=category_ids["Electronics"],
                        image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800"
                    ),
                    Product(
                        name="Classic Sneakers",
                        description="Everyday lightweight sneakers.",
                        price=2999,
                        stock=25,
                        category_id=category_ids["Shoes"],
                        image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800"
                    ),
                    Product(
                        name="Minimal Backpack",
                        description="Modern backpack for college and work.",
                        price=1799,
                        stock=30,
                        category_id=category_ids["Fashion"],
                        image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800"
                    )
                ]

                db.session.add_all(products)

            db.session.commit()

    return app
