from flasgger import swag_from
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from validators import email as validate_email
from werkzeug.security import check_password_hash, generate_password_hash

from src.db import db, User
from src.constants.http_status_code import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT

auth = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth.post('/register')
@swag_from('./docs/auth/register.yml')
def register():
    MIN_PASSWORD_LEN: int = 6
    MIN_USERNAME_LEN: int = 3

    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')

    if len(password) < MIN_PASSWORD_LEN:
        return jsonify(
            {
                'errors': [
                    {
                    'status': '400',
                    'source': { 'pointer': '/api/v1/auth/register' },
                    'title':  'Invalid Password Length',
                    'detail': f'Password must be at least {MIN_PASSWORD_LEN} characters long.'
                    }
                ]
            }
        ), HTTP_400_BAD_REQUEST

    if len(username) < MIN_USERNAME_LEN:
        return jsonify(
            {
                'errors': [
                    {
                    'status': '400',
                    'source': { 'pointer': '/api/v1/auth/register' },
                    'title':  'Invalid Username Length',
                    'detail': f'Username must be at least {MIN_USERNAME_LEN} characters long.'
                    }
                ]
            }
        ), HTTP_400_BAD_REQUEST

    if not username.isalnum() or ' ' in username:
        return jsonify(
            {
                'errors': [
                    {
                    'status': '400',
                    'source': { 'pointer': '/api/v1/auth/register' },
                    'title':  'Invalid Username',
                    'detail': f'Username should be alphanumeric.'
                    }
                ]
            }
        ), HTTP_400_BAD_REQUEST

    if not validate_email(email):
        return jsonify(
            {
                'errors': [
                    {
                    'status': '400',
                    'source': { 'pointer': '/api/v1/auth/register' },
                    'title':  'Invalid Email',
                    'detail': 'A valid email address is required.'
                    }
                ]
            }
        ), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify(
            {
                'errors': [
                    {
                    'status': '409',
                    'source': { 'pointer': '/api/v1/auth/register' },
                    'title':  'Email Already Exist',
                    'detail': f'Email address {email} already exists, please provide an unique email address.'
                    }
                ]
            }
        ), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first() is not None:
        return jsonify(
            {
                'errors': [
                    {
                    'status': '409',
                    'source': { 'pointer': '/api/v1/auth/register' },
                    'title':  'Username Already Exist',
                    'detail': f'Username {username} already exists, please provide an unique username.'
                    }
                ]
            }
        ), HTTP_409_CONFLICT

    pwd_hash = generate_password_hash(password)

    user = User(
        username = username,
        password = pwd_hash,
        email = email
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({'data': {'username': user.username, 'email': user.email}}), HTTP_201_CREATED


@auth.post('/login')
@swag_from('./docs/auth/login.yml')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = User.query.filter_by(email=email).first()

    if user is not None and check_password_hash(user.password, password):
        refresh = create_refresh_token(identity=user.id)
        access = create_access_token(identity=user.id)

        return jsonify({
            'data': {
                'user': {
                    'refresh': refresh,
                    'access': access,
                    'username': user.username,
                    'email': user.email
                }
            }
        }), HTTP_200_OK

    return jsonify({
        'errors': [
            {
            'status': '401',
            'source': { 'pointer': '/api/v1/auth/login' },
            'title':  'Invalid Credential',
            'detail': f'Credential is invalid, please provide the correct credntials.'
            }
        ]
    }), HTTP_401_UNAUTHORIZED


@auth.get('/me')
@jwt_required()
def me():
    user_id = get_jwt_identity()

    user = User.query.filter_by(id=user_id).first()

    return jsonify({
        'data': {
            'username': user.username,
            'email': user.email
        }
    }), HTTP_200_OK


@auth.post('/token/refresh')
@jwt_required(refresh=True)
def refresh_user_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)

    return jsonify({
        'data': {
            'access': access
        }
    }), HTTP_200_OK
