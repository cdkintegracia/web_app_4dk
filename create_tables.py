from web_app_4dk import app, db

with app.app_context():
    db.create_all()
