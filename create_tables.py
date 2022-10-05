from web_app_4dk import app, db

with app.app_context():
    a = db.create_all()
    print('БД создана')
    print(a)
