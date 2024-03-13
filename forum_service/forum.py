from flask import request, jsonify
from dbConfig import app, db, PORT
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


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

    comments = relationship("Comments", backref="post_comments")

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
    
class Comments(db.Model):
    __tablename__ = "comments"
    comment_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, ForeignKey('posts.post_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_edit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    post = relationship("Posts", back_populates="comments")

    def json(self):
        return {
            "comment_id": self.comment_id,
            "post_id": self.post_id,
            "content": self.content,
            "creation_date": self.creation_date,
            "last_edit_date": self.last_edit_date,
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
    

@app.route("/addComment/<string:post_id>", methods=["POST"])
def addComment(post_id):
    post = Posts.query.get(post_id)
    if not post:
        return jsonify({"code": 404, "message": "Post not found."}), 404

    data = request.get_json()
    comment_id = data.get('comment_id')
    content = data.get('content')

    comment = Comments(post_id=post_id, comment_id=comment_id, content=content)

    try:
        db.session.add(comment)
        db.session.commit()
        return jsonify({"code": 201, "data": comment.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"An error occurred creating the comment: {str(e)}"}), 500
    

@app.route("/getComments/<string:post_id>")
def getComments(post_id):
    comments = Comments.query.filter_by(post_id=post_id).all()

    if comments:
        comments_data = [comment.json() for comment in comments]
        return jsonify({"code": 200, "data": comments_data}), 200
    else:
        return jsonify({"code": 404, "message": "No comments found for the post."}), 404
    

@app.route("/updateComment/<string:comment_id>", methods=["PUT"])
def updateComment(comment_id):
    comment = Comments.query.get(comment_id)

    if not comment:
        return jsonify({"code": 404, "message": "Comment not found."}), 404

    data = request.get_json()
    content = data.get('content')

    comment.content = content

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": comment.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"An error occurred updating the comment: {str(e)}"}), 500
    

@app.route("/deleteComment/<string:comment_id>", methods=["DELETE"])
def deleteComment(comment_id):
    comment = Comments.query.get(comment_id)

    if not comment:
        return jsonify({"code": 404, "message": "Comment not found."}), 404

    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({"code": 200, "message": "Comment deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"An error occurred deleting the comment: {str(e)}"}), 500





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
