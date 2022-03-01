
from flask import Flask,session,request,jsonify,abort,make_response
import jwt

from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import os
import secrets
from functools import wraps
from werkzeug.security import generate_password_hash,check_password_hash


secret_key = secrets.token_hex(16)
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+os.path.join(basedir, "data.db")
app.config['SECRET_KEY'] = secret_key

db = SQLAlchemy(app)


def require_api_token(func):
    @wraps(func)
    def check_token(*args, **kwargs):
        if 'Authorization' not in session:
            return make_response("Access denied")
        return func(*args, **kwargs)
    return check_token



from models import *


@app.route("/", methods = ["POST"])
def registration():
    username = request.json["username"]
    password = request.json["password"]
    if (username or password) is None:
        abort(400)
    user = User(username=username,password=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({"username": user.username})


@app.route("/login/", methods = ["POST"])
def login():
    auth = request.authorization
    user = db.session.query(User).filter_by(username=auth.username).first_or_404()
    if auth and check_password_hash(user.password, auth.password):
        token = jwt.encode({
            'us_id': user.id,
            'exp': datetime.utcnow() + timedelta(minutes=30),
        }, app.config['SECRET_KEY'])
        session['Authorization'] = token
        session['User'] = user.id
        return make_response(jsonify({'token': token}), 201)

    else:
        return make_response("Error!", 401)


@app.route("/category/", methods=["POST"])
@require_api_token
def category_add():
    name = request.json["name"]
    if bool(name):
        user = Category(name=name)
        db.session.add(user)
        db.session.commit()
        return make_response(jsonify({"category": name}))
    else:
        return make_response("Error")


@app.route("/news_add/", methods=["POST"])
@require_api_token
def news_add():
    title = request.json["title"]
    body = request.json["body"]
    category = request.json["category"]
    user = session["User"]
    if (title or body or category or user) is None:
        abort(400)
    news = News(title=title, body=body, category=category, user=user)
    db.session.add(news)
    db.session.commit()
    return make_response("Done!",201)


@app.route("/news/<int:pk>/", methods=["GET"])
def news(pk):
    return make_response(jsonify([i.serialize for i in News.query.filter_by(id=pk)]))


@app.route("/all_news/", methods = ["GET"])
def all_news():
    return make_response(jsonify([i.serialize for i in News.query.all()]))


@app.route("/delete_news/<int:pk>/", methods = ["GET"])
def delete_news(pk):
    News.query.filter_by(id=pk).delete()
    db.session.commit()
    return make_response("Done!",201)


@app.route("/update_news/<int:id>/", methods=["PUT"])
def update_news(id):
    title = request.json["title"]
    body = request.json["body"]
    category = request.json["category"]
    date = datetime.now()
    if not (title or body or category or date):
        abort(400)
    News.query.filter_by(id=id).update(dict(body=body, title=title, category=category, date=date))
    db.session.commit()
    return make_response("Done!", 201)


if __name__ == '__main__':
    app.run(debug=True)