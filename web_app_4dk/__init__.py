from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


sentry_sdk.init(
    dsn="https://5a6b1a7f3d23458fa751de233db25cd0@o4505186652717056.ingest.sentry.io/4505186654289920",
    integrations=[
        FlaskIntegration(),
    ],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

app = Flask(__name__)
app.secret_key = 'some very secret phrase for web_app_4dk'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////root/web_app_4dk/web_app_4dk/DataBase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)


import web_app_4dk.models
import web_app_4dk.routes



