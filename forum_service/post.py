from flask import request, jsonify
from dbConfig import app, db, PORT
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


class Posts(db.Model):
    __tablename__ = "posts"
    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_edit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    views = db.Column(db.Integer, nullable=False, default=0)
    replies = db.Column(db.Integer, nullable=False, default=0)

    def __init__(
        self,
        post_id,
        user_id,
        title,
        content,
        creation_date,
        last_edit_date,
        views,
        replies,
    ):
        self.post_id = post_id
        self.user_id = user_id
        self.title = title
        self.content = content
        self.creation_date = creation_date
        self.last_edit_date = last_edit_date
        self.views = views
        self.replies = replies

    def json(self):
        return {
            "post_id": self.post_id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "creation_date": self.creation_date,
            "last_edit_date": self.last_edit_date,
            "views": self.views,
            "replies": self.replies,
        }


@app.route("/getPosts")
def getPosts():
    posts = db.session.scalars(db.select(Posts)).all()
    if len(posts):
        return jsonify(
            {
                "code": 200,
                "data": {"posts": [post.json() for post in posts]},
            }
        )
    return jsonify({"code": 404, "message": "There are no posts."}), 404


@app.route("/getPost/<string:post_id>")
def getPost(post_id):

    post = db.session.scalars(
        db.select(Posts).filter_by(post_id=post_id).limit(1)
    ).first()

    if post:
        return jsonify({"code": 200, "data": post.json()})
    return jsonify({"code": 404, "message": "post not found."}), 404


@app.route("/addPost/<string:post_id>", methods=["POST"])
def addPost(post_id):
    if db.session.scalars(
        db.select(Posts).filter_by(post_id=post_id).limit(1)
    ).first():
        return (
            jsonify(
                {
                    "code": 400,
                    "data": {"post_id": post_id},
                    "message": "Post already exists.",
                }
            ),
            400,
        )

    data = request.get_json()
    post_id = data.get('post_id')  # Get 'post_id' value if exists
    if post_id:
        del data['post_id']  # Remove 'post_id' key from data dictionary
    post = Posts(post_id, **data)


    try:
        db.session.add(post)
        db.session.commit()
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"post_id": post_id},
                    "message": "An error occurred creating the post.",
                }
            ),
            500,
        )

    return jsonify({"code": 201, "data": post.json()}), 201


@app.route("/deletePost/<string:post_id>", methods=["DELETE"])
def deletePost(post_id):
    post = db.session.query(Posts).filter_by(post_id=post_id).first()
    if post:
        try:
            db.session.delete(post)
            db.session.commit()
            return (
                jsonify(
                    {
                        "code": 200,
                        "data": {"post_id": post_id},
                        "message": "Post deleted successfully.",
                    }
                ),
                200,
            )
        except:
            return (
                jsonify(
                    {
                        "code": 500,
                        "data": {"post_id": post_id},
                        "message": "An error occurred while deleting the post.",
                    }
                ),
                500,
            )
    else:
        return (
            jsonify(
                {
                    "code": 404,
                    "data": {"post_id": post_id},
                    "message": "Post not found.",
                }
            ),
            404,
        )
    
@app.route("/updatePost/<string:post_id>", methods=["PUT"])
def updatePost(post_id):
    post = Posts.query.get(post_id)

    if not post:
        return jsonify({"code": 404, "message": "Post not found."}), 404

    data = request.get_json()

    for key, value in data.items():
        setattr(post, key, value)

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": post.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"An error occurred updating the post: {str(e)}"}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
