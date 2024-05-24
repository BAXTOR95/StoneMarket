from datetime import datetime
from typing import List
from flask_login import UserMixin
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    """
    Represents a user in the system.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user.
        email (str): The email address of the user.
        password_hash (str): The hashed password of the user.
        is_active (bool): Indicates whether the user is active or not.
        last_login (DateTime): The date and time of the user's last login (optional).
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Item(db.Model):
    """
    Represents an item for sale.

    Attributes:
        id (int): The unique identifier for the item.
        name (str): The name of the item.
        description (str): The description of the item.
        price (float): The price of the item.
        image (str): The URL of the item's image.
    """

    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column(Float)
    image: Mapped[str] = mapped_column(String(200))

    def __repr__(self) -> str:
        return f"<Item {self.name}>"


class Order(db.Model):
    """
    Represents an order in the system.

    Attributes:
        id (int): The unique identifier for the order.
        user_id (int): The identifier of the user who placed the order.
        total_amount (float): The total amount of the order.
        items (str): A string representation of the items in the order.
        status (str): The status of the order (e.g., 'Pending', 'Completed').
    """

    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    total_amount: Mapped[float] = mapped_column(Float)
    items: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default='Pending')

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order {self.id} for user {self.user_id}>"


class CartItem(db.Model):
    """Represents an item in a user's cart.

    Attributes:
        id (int): The unique identifier for the cart item.
        user_id (int): The identifier of the user who added the item to the cart.
        item_id (int): The identifier of the item in the cart.
        quantity (int): The quantity of the item in the cart.
    """

    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey('items.id'))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped["User"] = relationship("User", back_populates="cart_items")
    item: Mapped["Item"] = relationship("Item")

    def __repr__(self) -> str:
        return f"<CartItem {self.id} for user {self.user_id}>"
