import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-secret')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "database.db")}')
SQLALCHEMY_TRACK_MODIFICATIONS = False
MQTT_BROKER_HOST = os.environ.get('MQTT_BROKER_HOST', 'localhost')
MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT', '1883'))
MQTT_USERNAME = os.environ.get('MQTT_USERNAME')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD')
MQTT_ENABLED = os.environ.get('MQTT_ENABLED', 'true').lower() in {'1', 'true', 'yes'}
