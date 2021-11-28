from os import getenv
from flasgger import Swagger, swag_from
from flask import Flask, redirect, jsonify
from flask_jwt_extended import JWTManager

from src.auth import auth
from src.bookmarks import bookmarks
from src.config.swagger import template, swagger_config
from src.constants.http_status_code import HTTP_302_FOUND, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from src.db import db, Bookmark


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=getenv('SECRET_KEY'),
            SQLALCHEMY_DATABASE_URI=getenv('SQLALCHEMY_DB_URI'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=getenv('JWT_SECRET_KEY'),
            SWAGGER={
                'ttile': 'Bookmarks API',
                'uiversion': 3
            }
        )
    else:
        app.config.from_mapping(
            test_config
        )

    db.app = app
    db.init_app(app)
    JWTManager(app)
    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    Swagger(
        app,
        config=swagger_config,
        template=template
    )

    @app.get('/api/v1/<short_url>')
    @swag_from('./docs/short_url.yml')
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()

        if bookmark is not None:
            bookmark.visits += 1
            db.session.commit()

        return redirect(bookmark.url), HTTP_302_FOUND

    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_error_404(error):
        return jsonify({
            'errors': [
                {
                    'status': '404',
                    'source': { 'pointer': '/'},
                    'title':  'Not Found',
                    'detail': (str(error).split(':')[1]).strip()
                }
            ]
        }), HTTP_404_NOT_FOUND

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_error_500(error):
        return jsonify({
            'errors': [
                {
                    'status': '500',
                    'source': { 'pointer': '/'},
                    'title':  'Internal Error',
                    'detail': str(error).strip()
                }
            ]
        }), HTTP_500_INTERNAL_SERVER_ERROR

    return app
