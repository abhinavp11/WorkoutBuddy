from flask import Flask

#The create app function, which returns the app so the flask_implementation file can run it.
def create_app():
    app = Flask(__name__,template_folder="template", static_folder="static")
    # assigning the folders where the CSS styles and the HTML templates can be found
    app.config['SECRET_KEY'] = 'csincindeccnsicnis'
    #creating the secret key - which secures the session data.

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    #creates blueprints (application components) for the app

    return app
