from flask import Blueprint, jsonify, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return jsonify({
        "message": "Welcome to the Flask API!",
        "status": "success"
        })

@bp.route('/hello/<name>')
def hello(name):
    return jsonify({
        "message": f"Hello, {name}!",
        "status": "success"
        })

