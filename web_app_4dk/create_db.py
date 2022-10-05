from web_app_4dk import db, app

with app.app_context():
    db.create_all()
