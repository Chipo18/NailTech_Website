from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path 
from flask_login import LoginManager, current_user

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'snjgndfigninfjigisg'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    @app.context_processor
    def inject_user():
        return dict(user=current_user)

    from .views import views
    app.register_blueprint(views, url_prefix='/')

    from .auth import auth
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Service, Booking

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    if not path.exists('Nailtech_website/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print('Created Database!')

            # ✅ Add this block:
            from .models import Service
            if not Service.query.first():
                test_service = Service(
                    name="Classic Manicure",
                    description="A basic nail treatment with polish.",
                    price=30.0,
                    image_url="/static/images/manicure.jpg"  # Use a real image or leave blank
                )
                db.session.add(test_service)
                db.session.commit()
                print("Sample service added.")




