from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()


class DeviceType(Enum):
    LIGHT = 'LIGHT'
    CURTAIN = 'CURTAIN'
    PLUG = 'PLUG'
    CAMERA = 'CAMERA'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rooms = db.relationship('Room', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    room_name = db.Column(db.String(120), nullable=False)

    user = db.relationship('User', back_populates='rooms')
    devices = db.relationship('Device', back_populates='room', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Room {self.room_name}>'


class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.String(17), primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False, index=True)
    device_name = db.Column(db.String(120), nullable=False)
    device_type = db.Column(db.Enum(DeviceType), nullable=False)
    current_state = db.Column(db.String(80), nullable=False, default='OFF')
    stream_url = db.Column(db.String(500), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    room = db.relationship('Room', back_populates='devices')

    def __repr__(self):
        return f'<Device {self.device_name}>'
