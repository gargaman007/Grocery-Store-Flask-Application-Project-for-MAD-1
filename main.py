
import os
from datetime import datetime

# Inside your view function
current_year = datetime.now().year

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import joinedload, sessionmaker
from werkzeug.utils import secure_filename

from models import (Admin, Base, Cart, CartItem, Category, Customer, Order,
                    Product)

# Define a directory for storing product images
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}  # Define allowed image file extensions

# Create an instance of the Flask app and configure the image upload settings

app = Flask(__name__)
app.secret_key = 'Secret_Key'  # Replace with a strong secret key
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB

current_year = datetime.now().year

# Database setup
DATABASE_URL = 'sqlite:///database/mygrocerystore.db'
engine = create_engine(DATABASE_URL)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

@app.route('/')
def index():
    # Query the products from the database
    db_session = DBSession()
    products = db_session.query(Product).all()
    db_session.close()
    
    # Render the 'index.html' template and pass the products
    return render_template('index.html', products=products)


@app.route('/admin_home')
def admin_home():
    # Check if the admin is logged in
    if 'admin_id' in session:
        return render_template('admin_home.html')
    else:
        return redirect('/admin')  # Redirect to admin login if not logged in

# Registration and Login routes for Customers
# Registration and Login routes for Customers
@app.route('/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        db_session = DBSession()
        existing_customer = db_session.query(Customer).filter_by(username=username).first()
        if existing_customer:
            db_session.close()
            return "Username already exists. Please choose a different one."

        # Create a new customer
        new_customer = Customer(username=username, password=password)
        db_session.add(new_customer)
        db_session.commit()
        db_session.close()
        return redirect('/login')

    return render_template('customer_register.html')

@app.route('/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db_session = DBSession()
        customer = db_session.query(Customer).filter_by(username=username, password=password).first()
        db_session.close()

        if customer:
            # Store customer info in the session
            session['customer_id'] = customer.userid
            return redirect('/')
        else:
            return "Login failed. Please check your username and password."

    return render_template('customer_login.html', current_year=current_year)


# Route for logging out
@app.route('/logout')
def logout():
    # Clear the user session
    session.clear()
    # Redirect to the index page or any other desired page after logout
    return redirect('/')


# Login route for Admin
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db_session = DBSession()
        admin = db_session.query(Admin).filter_by(username=username, password=password).first()
        db_session.close()

        if admin:
            # Store admin info in the session
            session['admin_id'] = admin.adminid
            return redirect('/admin_home')  # Redirect to admin home on successful login
        else:
            return "Login failed. Please check your username and password."

    return render_template('admin_login.html')

# Logout route for Admin
@app.route('/admin_logout')
def admin_logout():
    # Check if the admin is logged in
    if 'admin_id' in session:
        # Remove admin information from the session
        session.pop('admin_id', None)
    
    # Optionally, you can redirect the admin to the login page or any other page
    return redirect('/admin')

# Add this route to your Flask application
@app.route('/manage_customers')
def manage_customers():
    # Retrieve the list of customers from the database
    db_session = DBSession()
    customers = db_session.query(Customer).all()
    db_session.close()
    
    # Render the manage_customers.html template and pass the customers
    return render_template('manage_customers.html', customers=customers)

# Add this route to your Flask application
@app.route('/delete_customer/<int:customer_id>')
def delete_customer(customer_id):
    # Delete the customer with the specified customer_id from the database
    db_session = DBSession()
    customer = db_session.query(Customer).filter_by(userid=customer_id).first()
    if customer:
        db_session.delete(customer)
        db_session.commit()
    db_session.close()
    
    # Redirect back to the manage_customers page
    return redirect('/manage_customers')

@app.route('/manage_admins', methods=['GET', 'POST'])
def manage_admins():
    # Check if the user is logged in as an admin
    if 'admin_id' not in session:
        return redirect('/admin')

    db_session = DBSession()

    if request.method == 'POST':
        if 'create_admin' in request.form:
            # Create a new admin
            username = request.form['admin_username']
            password = request.form['admin_password']
            
            # Check if the username already exists
            existing_admin = db_session.query(Admin).filter_by(username=username).first()
            if existing_admin:
                flash("Admin with the same username already exists.", 'danger')
            else:
                new_admin = Admin(username=username, password=password)
                db_session.add(new_admin)
                db_session.commit()
                flash("Admin created successfully.", 'success')
                return redirect('/admin')  # Redirect to admin login after creating admin

        elif 'delete_admin' in request.form:
            admin_id_to_delete = int(request.form['delete_admin'])
            
            # Ensure the first admin cannot be deleted
            if admin_id_to_delete != 1:
                admin_to_delete = db_session.query(Admin).filter_by(adminid=admin_id_to_delete).first()
                if admin_to_delete:
                    db_session.delete(admin_to_delete)
                    db_session.commit()
                    flash("Admin deleted successfully.", 'success')
                else:
                    flash("Admin not found.", 'danger')
            else:
                flash("Cannot delete the first admin.", 'danger')

    admins = db_session.query(Admin).all()
    db_session.close()

    return render_template('manage_admins.html', admins=admins)


@app.route('/manage_categories', methods=['GET', 'POST'])
def manage_categories():
    # Check if the user is logged in as an admin
    if 'admin_id' not in session:
        return redirect('/admin_login')

    db_session = DBSession()
    categories = db_session.query(Category).all()

    if request.method == 'POST':
        if 'delete_category' in request.form:
            category_id_to_delete = int(request.form['delete_category'])

            # Check if there are any products associated with the category
            products_in_category = db_session.query(Product).filter_by(category_id=category_id_to_delete).first()
            if products_in_category:
                flash("Category cannot be deleted as it has associated products.", 'danger')
            else:
                category_to_delete = db_session.query(Category).filter_by(category_id=category_id_to_delete).first()
                if category_to_delete:
                    db_session.delete(category_to_delete)
                    db_session.commit()
                    flash("Category deleted successfully.", 'success')
                    return redirect('/manage_categories')  # Redirect after successful deletion
                else:
                    flash("Category not found.", 'danger')

    # Close the session after all database operations are done
    db_session.close()

    return render_template('manage_categories.html', categories=categories)



@app.route('/create_category', methods=['GET', 'POST'])
def create_category():
    # Check if the user is logged in as an admin
    if 'admin_id' not in session:
        return redirect('/admin_login')

    db_session = DBSession()

    if request.method == 'POST':
        category_name = request.form['new_category_name']

        existing_category = db_session.query(Category).filter_by(category_name=category_name).first()
        if existing_category:
            flash("Category with the same name already exists.", 'danger')
        else:
            new_category = Category(category_name=category_name)
            db_session.add(new_category)
            db_session.commit()
            flash("Category created successfully.", 'success')
            return redirect('/manage_categories')

    db_session.close()

    return render_template('create_category.html')

@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    # Check if the user is logged in as an admin
    if 'admin_id' not in session:
        return redirect('/admin_login')

    db_session = DBSession()

    category = db_session.query(Category).filter_by(category_id=category_id).first()
    if not category:
        flash("Category not found.", 'danger')
        return redirect('/manage_categories')

    if request.method == 'POST':
        new_category_name = request.form['edit_category_name']

        existing_category = db_session.query(Category).filter_by(category_name=new_category_name).first()
        if existing_category:
            flash("Category with the same name already exists.", 'danger')
        else:
            category.category_name = new_category_name
            db_session.commit()
            flash("Category edited successfully.", 'success')
            return redirect('/manage_categories')

    db_session.close()

    return render_template('edit_category.html', category=category)



# Route to manage products (show all products, add new product)
@app.route('/manage_products', methods=['GET', 'POST'])
def manage_products():
    # Check if the user is logged in as an admin
    if 'admin_id' not in session:
        return redirect('/admin_login')
    db_session = DBSession()
    # Use joinedload to load the category relationship
    products = db_session.query(Product).options(joinedload(Product.category)).all()
    categories = db_session.query(Category).all()
    if request.method == 'POST':
        if 'delete_product' in request.form:
            product_id_to_delete = int(request.form['delete_product'])
            product_to_delete = db_session.query(Product).filter_by(product_id=product_id_to_delete).first()
            if product_to_delete:
                # Delete product image file if it exists
                if product_to_delete.image_path:
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], product_to_delete.image_path)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                db_session.delete(product_to_delete)
                db_session.commit()
                flash("Product deleted successfully.", 'success')
                # Redirect to the manage_products route after deletion
                return redirect(url_for('manage_products'))
    # Close the session after rendering the template
    db_session.close()
    return render_template('manage_products.html', products=products, categories=categories)



# Route to create a new product
@app.route('/create_product', methods=['GET', 'POST'])
def create_product():
    # Check if the user is logged in as an admin
    if 'admin_id' not in session:
        return redirect('/admin_login')

    db_session = DBSession()
    categories = db_session.query(Category).all()

    if request.method == 'POST':
        product_name = request.form['product_name']
        product_price = float(request.form['product_price'])
        description = request.form['description']
        category_id = int(request.form['category_id'])

        # Handle image upload
        if 'product_image' in request.files:
            image_file = request.files['product_image']
            if image_file.filename != '':
                if 'image' not in image_file.mimetype:
                    flash("Invalid file format. Please upload an image.", 'danger')
                elif not allowed_file(image_file.filename):
                    flash("Invalid file extension. Allowed extensions are jpg, jpeg, png, gif.", 'danger')
                else:
                    # Securely save the image file
                    filename = secure_filename(image_file.filename)
                    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_path = filename
        else:
            image_path = None

        # Create a new product
        new_product = Product(
            product_name=product_name,
            product_price=product_price,
            description=description,
            category_id=category_id,
            image_path=image_path  # Save the image path in the database
        )
        db_session.add(new_product)
        db_session.commit()
        flash("Product created successfully.", 'success')
        return redirect('/manage_products')

    db_session.close()

    return render_template('create_product.html', categories=categories)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to edit an existing product
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    # Check if the user is logged in as an admin
    if 'admin_id' not in session:
        return redirect('/admin_login')

    db_session = DBSession()

    # Query the product to edit, eagerly loading the 'category' relationship
    product_to_edit = db_session.query(Product).options(joinedload(Product.category)).filter_by(product_id=product_id).first()

    if product_to_edit is None:
        flash("Product not found.", 'danger')
        return redirect('/manage_products')

    categories = db_session.query(Category).all()

    if request.method == 'POST':
        product_name = request.form['product_name']
        product_price = float(request.form['product_price'])
        description = request.form['description']
        category_id = int(request.form['category_id'])

        # Handle image upload
        if 'product_image' in request.files:
            image_file = request.files['product_image']
            if image_file.filename != '':
                if 'image' not in image_file.mimetype:
                    flash("Invalid file format. Please upload an image.", 'danger')
                elif not allowed_file(image_file.filename):
                    flash("Invalid file extension. Allowed extensions are jpg, jpeg, png, gif.", 'danger')
                else:
                    # Securely save the image file
                    filename = secure_filename(image_file.filename)
                    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_path = filename
                    # Remove the old image file if it exists
                    if product_to_edit.image_path:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product_to_edit.image_path)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
        else:
            # If no new image was uploaded, keep the existing image path
            image_path = product_to_edit.image_path

        # Update the product
        product_to_edit.product_name = product_name
        product_to_edit.product_price = product_price
        product_to_edit.description = description
        product_to_edit.category_id = category_id
        product_to_edit.image_path = image_path  # Update the image path

        db_session.commit()
        flash("Product updated successfully.", 'success')
        return redirect('/manage_products')

    db_session.close()

    return render_template('edit_product.html', product=product_to_edit, categories=categories)

# Add a route to view all categories
@app.route('/view_categories')
def view_categories():
    db_session = DBSession()
    categories = db_session.query(Category).all()
    db_session.close()
    return render_template('view_categories.html', categories=categories)

# Add a route to view products by category
@app.route('/view_products/<int:category_id>')
def view_products_by_category(category_id):
    db_session = DBSession()
    category = db_session.query(Category).filter_by(category_id=category_id).first()
    if category:
        products = db_session.query(Product).filter_by(category_id=category_id).all()
    else:
        products = []
    db_session.close()
    return render_template('view_products_by_category.html', category=category, products=products)



# Route to view the cart
@app.route('/cart', methods=['GET', 'POST'])
def view_cart():
    # Check if the user is logged in as a customer
    if 'customer_id' not in session:
        flash("Please log in to view your cart.", 'danger')
        return redirect('/login')  # Redirect to the login page if not logged in

    customer_id = session['customer_id']
    db_session = DBSession()
    customer_cart = db_session.query(Cart).filter_by(customer_id=customer_id).first()
    cart_items = []
    cart_total = 0

    if customer_cart:
        # Load the CartItem objects and their associated Product objects in the same session
        cart_items = db_session.query(CartItem).filter_by(cart_id=customer_cart.cart_id).options(joinedload(CartItem.product)).all()
        # Calculate the total price
        cart_total = sum(cart_item.price * cart_item.quantity for cart_item in cart_items)

    if request.method == 'POST':
        action = request.form.get('action')
        cart_item_id = int(request.form.get('cart_item_id'))

        if action == 'add':
            # ... not needed
            return

        elif action == 'remove':
            # Handle removing items from the cart
            cart_item = db_session.query(CartItem).filter_by(cart_item_id=cart_item_id).first()

            if cart_item:
                db_session.delete(cart_item)
                db_session.commit()
                flash("Product removed from the cart.", 'success')
                return render_template('cart.html')
            else:
                flash("Product not found in the cart.", 'danger')

    # Close the session
    db_session.close()

    return render_template('cart.html', cart_items=cart_items,cart_total=cart_total)


# Route to add a product to the cart
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    # Check if the user is logged in as a customer
    if 'customer_id' not in session:
        return redirect('/login')  # Redirect to the login page if not logged in

    customer_id = session['customer_id']
    db_session = DBSession()
    
    # Check if the customer already has a cart, create one if not
    customer_cart = db_session.query(Cart).filter_by(customer_id=customer_id).first()
    if not customer_cart:
        customer_cart = Cart(customer_id=customer_id)
        db_session.add(customer_cart)
        db_session.commit()

    # Retrieve the product with the specified product_id
    product = db_session.query(Product).filter_by(product_id=product_id).first()

    if product:
        # Check if the product is already in the cart, update quantity if so
        existing_cart_item = db_session.query(CartItem).filter_by(cart_id=customer_cart.cart_id, product_id=product_id).first()
        if existing_cart_item:
            existing_cart_item.quantity += 1
        else:
            cart_item = CartItem(cart_id=customer_cart.cart_id, product_id=product_id, quantity=1, price=product.product_price)
            db_session.add(cart_item)

        db_session.commit()
        db_session.close()
        flash("Product added to the cart.", 'success')
        return redirect('/cart')
    else:
        db_session.close()
        flash("Product not found.", 'danger')

    return redirect('/cart')  # Redirect to the cart page


@app.route('/order_product/<int:product_id>', methods=['GET', 'POST'])
def order_product(product_id):
    try:
        # Check if the user is logged in as a customer
        if 'customer_id' not in session:
            flash("Please log in to order products.", 'danger')
            return redirect('/login')  # Redirect to the login page if not logged in

        customer_id = session['customer_id']
        db_session = DBSession()

        # Retrieve the product with the specified product_id
        product = db_session.query(Product).filter_by(product_id=product_id).first()

        if product:
            # Check if the product is already in the cart, update quantity if so
            customer_cart = db_session.query(Cart).filter_by(customer_id=customer_id).first()
            if customer_cart:
                existing_cart_item = db_session.query(CartItem).filter_by(
                    cart_id=customer_cart.cart_id,
                    product_id=product_id
                ).first()
                if existing_cart_item:
                    existing_cart_item.quantity += 1
                    flash("Product quantity updated in the cart.", 'success')
                else:
                    cart_item = CartItem(
                        cart_id=customer_cart.cart_id,
                        product_id=product_id,
                        quantity=1,
                        price=product.product_price
                    )
                    db_session.add(cart_item)
                    flash("Product added to the cart.", 'success')

                db_session.commit()
                return redirect('/cart')
            else:
                flash("Cart not found. Please create a cart before ordering products.", 'danger')
        else:
            flash("Product not found.", 'danger')

        return redirect('/')  # Redirect to the home page if there's an error or if the product doesn't exist
    except Exception as e:
        # Handle any exceptions, log them, and provide a generic error message
        print(str(e))
        flash("An error occurred while ordering the product. Please try again later.", 'danger')
        return redirect('/cart')
    finally:
        db_session.close()  # Make sure to close the session in all cases

# Route for updating the cart
@app.route('/update_cart/<int:cart_item_id>', methods=['POST'])
def update_cart(cart_item_id):
    try:
        # Check if the user is logged in as a customer
        if 'customer_id' not in session:
            flash("Please log in to update your cart.", 'danger')
            return redirect('/login')  # Redirect to the login page if not logged in

        customer_id = session['customer_id']
        db_session = DBSession()

        # Retrieve the cart item with the specified cart_item_id
        cart_item = db_session.query(CartItem).filter_by(cart_item_id=cart_item_id).first()

        if cart_item:
            new_quantity = int(request.form.get('quantity'))
            if new_quantity <= 0:
                # If the user sets the quantity to 0 or less, remove the item from the cart
                db_session.delete(cart_item)
                flash("Product removed from the cart.", 'success')
            else:
                cart_item.quantity = new_quantity
                flash("Cart updated successfully.", 'success')

            db_session.commit()
            return redirect('/cart')
        else:
            flash("Cart item not found.", 'danger')

        return redirect('/cart')  # Redirect to the cart page if there's an error or if the cart item doesn't exist
    except Exception as e:
        # Handle any exceptions, log them, and provide a generic error message
        print(str(e))
        flash("An error occurred while updating the cart. Please try again later.", 'danger')
        return redirect('/cart')
    finally:
        db_session.close()  # Make sure to close the session in all cases


# Route for managing orders
@app.route('/manage_orders')
def manage_orders():
    # Retrieve order details from the database
    
    db_session = DBSession()
    orders = db_session.query(Order).all()
    
    return render_template('manage_orders.html', orders=orders)

# Route for checkout
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Check if the user is logged in as a customer
    if 'customer_id' not in session:
        flash("Please log in to proceed with checkout.", 'danger')
        return redirect('/login')  # Redirect to the login page if not logged in

    if request.method == 'POST':
        customer_id = session['customer_id']
        address = request.form['address']
        phone = request.form['phone']

        # Get the cart items for the customer
        cart_items = get_cart_items(customer_id)

        if not cart_items:
            flash("Your cart is empty. Add products to your cart before checking out.", 'danger')
            return redirect('/cart')

        try:
            db_session = DBSession()

            # Iterate through cart items and create an order for each
            for cart_item in cart_items:
                order = Order(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    address=address,
                    phone_number=phone,
                    customer_id=customer_id  # Store the customer_id in the order
                )
                db_session.add(order)

            db_session.commit()

            # Clear the customer's cart after placing the order
            clear_cart(customer_id)

            flash("Order placed successfully. Thank you!", 'success')
            return redirect('/')  # Redirect to the home page or order history page

        except Exception as e:
            # Handle any exceptions, log them, and provide a generic error message
            print(str(e))
            flash("An error occurred while placing the order. Please try again later.", 'danger')
            return redirect('/cart')
        finally:
            db_session.close()  # Make sure to close the session in all cases

    return render_template('checkout.html')

# Function to retrieve cart items for a customer
def get_cart_items(customer_id):
    db_session = DBSession()
    customer_cart = db_session.query(Cart).filter_by(customer_id=customer_id).first()
    cart_items = []

    if customer_cart:
        # Load the CartItem objects and their associated Product objects in the same session
        cart_items = db_session.query(CartItem).filter_by(cart_id=customer_cart.cart_id).options(joinedload(CartItem.product)).all()

    db_session.close()
    return cart_items

# Add this function to your Flask application

def clear_cart(customer_id):
    try:
        db_session = DBSession()
        customer_cart = db_session.query(Cart).filter_by(customer_id=customer_id).first()

        if customer_cart:
            # Delete all cart items associated with the customer's cart
            db_session.query(CartItem).filter_by(cart_id=customer_cart.cart_id).delete()
            db_session.commit()
    except Exception as e:
        # Handle any exceptions, log them, and provide a generic error message
        print(str(e))
    finally:
        db_session.close()



@app.route('/customer/orders', methods=['GET'])
def customer_orders():
    # Check if the user is logged in as a customer
    if 'customer_id' not in session:
        flash("Please log in to view your orders.", 'danger')
        return redirect('/login')  # Redirect to the login page if not logged in

    try:
        db_session = DBSession()
        # Get the customer's orders using the current SQLAlchemy session
        customer_id = session['customer_id']
        customer_orders = db_session.query(Order).filter_by(customer_id=customer_id).all()

        return render_template('customer_orders.html', orders=customer_orders)

    except Exception as e:
        # Handle any exceptions here (e.g., logging, displaying an error message)
        print(str(e))
        flash("An error occurred while fetching your orders. Please try again later.", 'danger')
        return redirect('/')

@app.route('/search', methods=['GET'])
def search():
    # Get the search query from the URL parameter 'query'
    query = request.args.get('query', '')

    # Perform the search in your database
    db_session = DBSession()
    products = db_session.query(Product).filter(
        or_(
            Product.product_name.ilike(f'%{query}%'),
            Product.description.ilike(f'%{query}%'),
            Product.category.has(Category.category_name.ilike(f'%{query}%'))
        )
    ).all()
    
    db_session.close()

    # Render a template to display the search results
    return render_template('search_results.html', query=query, products=products)

@app.route('/api/products')
def get_products_api():
    db_session = DBSession()
    products = db_session.query(Product).all()
    db_session.close()
    
    # Serialize products into JSON format
    products_data = [
        {
            'product_id': product.product_id,
            'product_name': product.product_name,
            'product_price': product.product_price,
            'description': product.description,
            'category_id': product.category_id,
            'image_path': product.image_path
        }
        for product in products
    ]
    
    return jsonify(products_data)

@app.route('/api/categories')
def get_categories_api():
    db_session = DBSession()
    categories = db_session.query(Category).all()
    db_session.close()
    
    # Serialize categories into JSON format
    categories_data = [{'id': category.category_id, 'name': category.category_name} for category in categories]
    
    return jsonify(categories_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)
