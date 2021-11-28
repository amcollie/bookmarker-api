from flasgger import swag_from
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
import validators

from src.constants.http_status_code import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from src.db import Bookmark, db

bookmarks = Blueprint('bookmarks', __name__, url_prefix='/api/v1/bookmarks')

@bookmarks.post('/')
@jwt_required()
def create_bookmark():
    current_user = get_jwt_identity()
    body = request.json.get('body', '')
    url = request.json.get('url', '')

    if not validators.url(url):
        return jsonify({
            'errors': [
                {
                    'status': '400',
                    'source': { 'pointer': '/api/v1/bookmark' },
                    'title':  'Invalid URL',
                    'detail': 'URL is invalid, please provide a value URL.'
                }
            ]
        }), HTTP_400_BAD_REQUEST

    if Bookmark.query.filter_by(url=url).first() is not None:
        return jsonify({
            'errors': [
                {
                    'status': '409',
                    'source': { 'pointer': '/api/v1/bookmark' },
                    'title':  'URL Already Exists',
                    'detail': 'URL is already exist, please provide another url.'
                }
            ]
        }), HTTP_409_CONFLICT

    bookmark = Bookmark(url=url, body=body, user_id=current_user)

    db.session.add(bookmark)
    db.session.commit()
    return jsonify({
        'data': {
            'bookmark': {
                'id': bookmark.id,
                'url': bookmark.url,
                'short_url': bookmark.short_url,
                'visits': bookmark.visits,
                'body': bookmark.body,
                'created at': bookmark.created_at,
                'updated_at': bookmark.updated_at
            }
        }
    }), HTTP_201_CREATED


@bookmarks.get('/')
@jwt_required()
def get_bookmarks():
    current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    bookmarks = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)

    data = []
    for bookmark in bookmarks.items:
        data.append({
            'id': bookmark.id,
            'url': bookmark.url,
            'short_url': bookmark.short_url,
            'visits': bookmark.visits,
            'body': bookmark.body,
            'created at': bookmark.created_at,
            'updated_at': bookmark.updated_at
        })

    meta = {
        'page': bookmarks.page,
        'pages': bookmarks.pages,
        'total_pages': bookmarks.total,
        'prev_page': bookmarks.prev_num,
        'next_page': bookmarks.next_num,
        'has_next': bookmarks.has_next,
        'has_prev': bookmarks.has_prev
    }
    return jsonify({
        'data': {'bookmarks': data},
        'meta': meta
    }), HTTP_200_OK


@bookmarks.get('/<int:bookmark_id>')
@jwt_required()
def get_bookmark(bookmark_id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=bookmark_id).first()

    if not bookmark:
        return jsonify({
            'errors': [
                {
                    'status': '404',
                    'source': { 'pointer': '/api/v1/bookmark' },
                    'title':  'Bookmark Not Found',
                    'detail': f'Unable to find bookmark with id: {bookmark_id}.'
                }
            ]
        }), HTTP_404_NOT_FOUND

    return jsonify({
        'data': {
            'bookmark': {
                'id': bookmark.id,
                'url': bookmark.url,
                'short_url': bookmark.short_url,
                'visits': bookmark.visits,
                'body': bookmark.body,
                'created at': bookmark.created_at,
                'updated_at': bookmark.updated_at
            }
        }
    }), HTTP_200_OK


@bookmarks.put("/<int:bookmark_id>")
@bookmarks.patch("/<int:bookmark_id>")
@jwt_required()
def update_bookmark(bookmark_id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=bookmark_id).first()

    if not bookmark:
        return jsonify({
            'errors': [
                {
                    'status': '404',
                    'source': { 'pointer': '/api/v1/bookmark' },
                    'title':  'Bookmark Not Found',
                    'detail': f'Unable to find bookmark with id: {bookmark_id}.'
                }
            ]
        }), HTTP_404_NOT_FOUND

    body = request.json.get('body', '')
    url = request.json.get('url', '')

    if not validators.url(url):
        return jsonify({
            'errors': [
                {
                    'status': '400',
                    'source': { 'pointer': '/api/v1/bookmark' },
                    'title':  'Invalid URL',
                    'detail': 'URL is invalid, please provide a value URL.'
                }
            ]
        }), HTTP_400_BAD_REQUEST

    bookmark.url = url
    bookmark.body = body

    db.session.commit()

    return jsonify({
        'data': {
            'bookmark': {
                'id': bookmark.id,
                'url': bookmark.url,
                'short_url': bookmark.short_url,
                'visits': bookmark.visits,
                'body': bookmark.body,
                'created at': bookmark.created_at,
                'updated_at': bookmark.updated_at
            }
        }
    }), HTTP_200_OK


@bookmarks.delete("/<int:bookmark_id>")
@jwt_required()
def delete_bookmark(bookmark_id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=bookmark_id).first()

    if not bookmark:
        return jsonify({
            'errors': [
                {
                    'status': '404',
                    'source': { 'pointer': '/api/v1/bookmark' },
                    'title':  'Bookmark Not Found',
                    'detail': f'Unable to find bookmark with id: {bookmark_id}.'
                }
            ]
        }), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT


@bookmarks.get('/stats')
@jwt_required()
@swag_from('./docs/bookmarks/stats.yml')
def get_stats():
    current_user = get_jwt_identity()
    data = []

    items = Bookmark.query.filter_by(user_id=current_user).all()

    for item in items:
        print(item)
        new_link = {
            'visits': item.visits,
            'url': item.url,
            'id': item.id,
            'short_url': item.short_url
        }

        data.append(new_link)

    return jsonify({'data': data}), HTTP_200_OK
