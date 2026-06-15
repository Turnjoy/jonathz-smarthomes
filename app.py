import json
import os
import secrets
from datetime import datetime
from functools import wraps

import paho.mqtt.client as mqtt
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config.branding import load_brand_config
from database.db_init import init_db
from database.models import Device, DeviceType, Room, User, db

app = Flask(__name__)
app.config.from_object('config.settings')
app.brand = load_brand_config(app.static_folder)
app.mqtt_client = None

init_db(app)


@app.context_processor
def inject_brand():
    return {"brand": app.brand}


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


@app.route('/')
def marketing():
    smart_kits = [
        {
            "name": "Curtain Automation",
            "type": "CURTAIN",
            "description": "Motorized curtain control with instant open and close commands.",
            "image": "/static/img/IMG-20260529-WA0008.jpg",
        },
        {
            "name": "Lighting & Plug Control",
            "type": "LIGHT",
            "description": "Low-latency switching for lights, sockets, and relay modules.",
            "image": "/static/img/WhatsApp Image 2026-05-16 at 2.57.23 PM.jpeg",
        },
        {
            "name": "Camera Monitoring",
            "type": "CAMERA",
            "description": "Live stream slots for camera endpoints already mapped to each home.",
            "image": app.brand["assets"]["hero"] or "/static/img/IMG-20260529-WA0008.jpg",
        },
    ]
    return render_template('marketing.html', smart_kits=smart_kits)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or len(password) < 8:
            flash('Enter your name, email, and a password of at least 8 characters.', 'error')
            return render_template('signup.html'), 400

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
            return render_template('signup.html'), 409

        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        session.clear()
        session['user_id'] = user.id
        flash('Your smart home console is ready.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'error')
            return render_template('login.html'), 401

        session.clear()
        session['user_id'] = user.id
        return redirect(request.args.get('next') or url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('marketing'))


@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    rooms = (
        Room.query.filter_by(user_id=user.id)
        .order_by(Room.room_name.asc())
        .all()
    )
    return render_template('dashboard.html', user=user, rooms=rooms, device_types=DeviceType)


@app.route('/api/device/control', methods=['POST'])
@login_required
def control_device():
    payload = request.get_json(silent=True) or {}
    device_id = payload.get('device_id')
    action = str(payload.get('action', '')).upper()

    if not device_id or not action:
        return jsonify({"error": "device_id and action are required"}), 400

    device = (
        Device.query.join(Room)
        .filter(Device.id == device_id, Room.user_id == session['user_id'])
        .first()
    )
    if not device:
        abort(404)

    allowed_actions = {
        DeviceType.LIGHT: {'ON', 'OFF', 'TOGGLE'},
        DeviceType.PLUG: {'ON', 'OFF', 'TOGGLE'},
        DeviceType.CURTAIN: {'OPEN', 'CLOSE', 'STOP'},
        DeviceType.CAMERA: {'START', 'STOP', 'SNAPSHOT'},
    }
    if action not in allowed_actions[device.device_type]:
        return jsonify({"error": f"{action} is not valid for {device.device_type.value}"}), 422

    command = {
        "device_id": device.id,
        "device_type": device.device_type.value,
        "action": action,
        "current_state": device.current_state,
        "stream_url": device.stream_url,
        "issued_at": datetime.utcnow().isoformat() + "Z",
    }

    topic = f"smarthome/hardware/{device.id}/cmd"
    published = publish_mqtt(topic, command)
    return jsonify({"ok": True, "published": published, "topic": topic, "command": command})


@app.route('/api/device/status')
@login_required
def device_status():
    devices = (
        Device.query.join(Room)
        .filter(Room.user_id == session['user_id'])
        .all()
    )
    return jsonify({
        device.id: {
            "state": device.current_state,
            "updated_at": device.last_updated.isoformat() if device.last_updated else None,
        }
        for device in devices
    })


def publish_mqtt(topic, payload):
    client = app.mqtt_client
    if not client:
        return False
    result = client.publish(topic, json.dumps(payload), qos=1)
    return result.rc == mqtt.MQTT_ERR_SUCCESS


def on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe("smarthome/hardware/+/status", qos=1)


def on_message(client, userdata, message):
    try:
        topic_parts = message.topic.split("/")
        device_id = topic_parts[2]
        payload = json.loads(message.payload.decode("utf-8"))
        state = str(payload.get("state") or payload.get("current_state") or payload.get("status") or "").upper()
    except (IndexError, json.JSONDecodeError, UnicodeDecodeError):
        return

    if not state:
        return

    with app.app_context():
        device = db.session.get(Device, device_id)
        if device:
            device.current_state = state
            device.last_updated = datetime.utcnow()
            db.session.commit()


def start_mqtt_client():
    if not app.config.get("MQTT_ENABLED", True):
        return
    if app.mqtt_client:
        return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"smarthome-web-{secrets.token_hex(4)}")
    username = app.config.get("MQTT_USERNAME")
    password = app.config.get("MQTT_PASSWORD")
    if username:
        client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect_async(app.config["MQTT_BROKER_HOST"], app.config["MQTT_BROKER_PORT"], keepalive=60)
        client.loop_start()
        app.mqtt_client = client
    except OSError:
        app.logger.warning("MQTT broker is unavailable; web app will keep running without live publish.")


start_mqtt_client()


if __name__ == '__main__':
    app.run(debug=True)
