from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(1000))
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300))  # Store image path or URL
    
    bookings = db.relationship('Booking', backref='service', cascade="all, delete-orphan")
    working_hours = db.relationship('WorkingHours', backref='service', cascade="all, delete-orphan")

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    date_time = db.Column(db.DateTime, nullable=False)
    contact_info = db.Column(db.String(150))
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    firstName = db.Column(db.String(150))
    # Optional: add relationships
    bookings = db.relationship('Booking', backref='user')

from datetime import time

class WorkingHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weekday = db.Column(db.Integer, nullable=False)  # 0=Monday ... 6=Sunday
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    slot_time = db.Column(db.Time, nullable=False)  # each slot is a specific time



