# 🛍️ ShopSphere

A full-stack e-commerce web application built with **Python Flask, MySQL, SQLAlchemy, HTML, CSS, JavaScript, and Bootstrap**.

ShopSphere provides a complete online shopping experience with customer authentication, product browsing, wishlist, shopping cart, checkout, order tracking, and an administrative management system.

---

## ✨ Features

### 👤 Customer Features

- User registration and login
- Secure password hashing
- Product catalog
- Product search
- Category filtering
- Product details
- Product image display
- Wishlist management
- Shopping cart
- Cart quantity updates
- Stock validation
- Checkout
- Delivery information
- Multiple payment method selection
- Order confirmation
- Order history
- Order details
- Order status tracking
- Customer order cancellation
- Automatic stock restoration after cancellation

### ⚙️ Admin Features

- Secure admin login
- Admin dashboard
- Product management
- Product image upload
- Inventory management
- Product deletion protection
- User management
- Order management
- Order status updates
- Customer order details
- Revenue and order statistics

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Backend programming |
| Flask | Web framework |
| SQLAlchemy | ORM / Database management |
| MySQL | Relational database |
| PyMySQL | MySQL connection |
| HTML5 | Page structure |
| CSS3 | Styling |
| JavaScript | Client-side functionality |
| Bootstrap 5 | Responsive UI |
| Jinja2 | Template rendering |

---

## 📁 Project Structure

```text
ShopSphere_Flask_ECommerce/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── uploads/
│   │
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       ├── product_detail.html
│       ├── wishlist.html
│       ├── cart.html
│       ├── checkout.html
│       ├── order_confirmation.html
│       ├── orders.html
│       ├── order_detail.html
│       ├── admin.html
│       ├── admin_products.html
│       ├── admin_orders.html
│       ├── admin_order_detail.html
│       └── admin_users.html
│
├── .env.example
├── .gitignore
├── config.py
├── requirements.txt
├── run.py
└── README.md