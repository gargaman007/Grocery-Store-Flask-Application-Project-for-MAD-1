
from sqlalchemy import (Column, Float,  # Import Sequence for auto-increment
                        ForeignKey, Integer, Sequence, String, create_engine,
                        func)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

DATABASE_URL = 'sqlite:///mygrocerystore.db'
engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    userid = Column(Integer, Sequence('customer_id_seq'), primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

class Admin(Base):
    __tablename__ = 'admins'
    adminid = Column(Integer, Sequence('admin_id_seq'), primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(Integer, Sequence('category_id_seq'), primary_key=True, autoincrement=True)
    category_name = Column(String, nullable=False)

    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = 'products'
    product_id = Column(Integer, Sequence('product_id_seq'), primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey('categories.category_id'))
    product_name = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)
    description = Column(String)
    image_path = Column(String)

    category = relationship("Category", back_populates="products")

class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, Sequence('order_id_seq'), primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    quantity = Column(Integer, nullable=False)
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.userid'))  # Add a foreign key relationship
    
    # Define a relationship to the Product class
    product = relationship("Product")
    customer = relationship("Customer")  # Add a relationship to the Customer class
    
class Cart(Base):
    __tablename__ = 'carts'
    cart_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.userid'))
    
    # Define a one-to-many relationship to CartItem
    cart_items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    __tablename__ = 'cart_items'
    cart_item_id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.cart_id'))
    product_id = Column(Integer, ForeignKey('products.product_id'))
    quantity = Column(Integer)
    price = Column(Float)  # Price per unit at the time of adding to cart
    
    # Define a many-to-one relationship to Cart
    cart = relationship("Cart", back_populates="cart_items")
    
    # Define a relationship to the Product class
    product = relationship("Product")

Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()


# Check if the 'admin' user already exists
existing_admin = session.query(Admin).filter_by(username='admin').first()

if not existing_admin:
    # Create a new admin user
    admin = Admin(username='admin', password='admin')
    session.add(admin)
    session.commit()
    print("Admin user 'admin' with password 'admin' created successfully.")
else:
    print("Admin user 'admin' already exists in the database.")


session.commit()

print("Database tables created successfully.")
