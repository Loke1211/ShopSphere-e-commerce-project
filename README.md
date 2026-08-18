# ShopSphere

Full Stack E-Commerce Web Application built with Python Flask, MySQL, SQLAlchemy, HTML, CSS and JavaScript/Bootstrap.

## Features
- Authentication
- Product catalog
- Search and category filtering
- Wishlist
- Shopping cart
- Checkout and orders
- Admin dashboard
- Product/inventory management
- Order status management
- User management

## Local setup

1. Install Python 3.11+.
2. Install and start MySQL.
3. Create a database:
   `CREATE DATABASE shopsphere;`
4. Create and activate a virtual environment.
5. Run `pip install -r requirements.txt`.
6. Copy `.env.example` to `.env` and update your MySQL password.
7. Run `flask --app run.py seed`.
8. Run `python run.py`.
9. Open http://127.0.0.1:5000

Admin login:
Email: admin@shopsphere.com
Password: Admin@123
