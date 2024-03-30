from flask import request, jsonify
from dbConfig import app, db, PORT
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID


class Forums(db.Model):
    __tablename__ = "forums"
    concert_id = db.Column(db.String(255), primary_key=True)
    concert_name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String(255), nullable=False)

    posts = relationship("Posts", backref="forum")

    def __init__(self, concert_id, concert_name, user_id):
        self.concert_id = concert_id
        self.concert_name = concert_name
        self.user_id = user_id

    def json(self):
        return {
            "concert_id": self.concert_id,
            "concert_name": self.concert_name,
            "user_id": self.user_id,
        }


class Posts(db.Model):
    __tablename__ = "posts"
    post_id = db.Column(db.String(255), primary_key=True)
    concert_id = db.Column(
        db.String(255), db.ForeignKey("forums.concert_id"), nullable=False
    )
    user_id = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    edited_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    views = db.Column(db.Integer, nullable=False, default=0)
    replies = db.Column(db.Integer, nullable=False, default=0)

    comments = relationship("Comments", backref="post")

    def __init__(
        self,
        post_id,
        concert_id,
        user_id,
        title,
        content,
    ):
        self.post_id = post_id
        self.concert_id = concert_id
        self.user_id = user_id
        self.title = title
        self.content = content

    def json(self):
        return {
            "post_id": self.post_id,
            "concert_id": self.concert_id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
        }


class Comments(db.Model):
    __tablename__ = "comments"
    comment_id = db.Column(db.String(100), primary_key=True)
    post_id = db.Column(db.String(100), ForeignKey("posts.post_id"), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    edited_at = db.Column(db.DateTime, nullable=False, default=datetime.now())

    def json(self):
        return {
            "comment_id": self.comment_id,
            "post_id": self.post_id,
            "content": self.content,
            "user_id": self.user_id,
        }


@app.route("/api/v1/getPosts")
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


@app.route("/api/v1/getPostsByConcertId/<string:concert_id>")
def getPostsByUserId(concert_id):
    posts = db.session.scalars(db.select(Posts).filter_by(concert_id=concert_id)).all()
    if len(posts):
        return jsonify(
            {
                "code": 200,
                "data": {"posts": [post.json() for post in posts]},
            }
        )
    return jsonify({"code": 404, "message": "There are no posts."}), 404


@app.route("/api/v1/getPost/<string:post_id>")
def getPost(post_id):
    post = db.session.query(Posts).filter_by(post_id=post_id).first()

    if post:
        post.views += 1
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return (
                jsonify(
                    {
                        "code": 500,
                        "message": "An error occurred while updating views count.",
                    }
                ),
                500,
            )

        return jsonify({"code": 200, "data": post.json()})
    else:
        return jsonify({"code": 404, "message": "Post not found."}), 404


@app.route("/api/v1/addPost/<string:post_id>", methods=["POST"])
def addPost(post_id):
    if db.session.scalars(db.select(Posts).filter_by(post_id=post_id).limit(1)).first():
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
    post_id = data.get("post_id")  # Get concert_id from FE

    if post_id:
        del data["post_id"]  # Remove 'post_id' key from data dictionary
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


@app.route("/api/v1/deletePost/<string:post_id>", methods=["DELETE"])
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


@app.route("/api/v1/updatePost/<string:post_id>", methods=["PUT"])
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
        return (
            jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred updating the post: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/v1/addComment/<string:post_id>", methods=["POST"])
def addComment(post_id):
    post = Posts.query.get(post_id)
    if not post:
        return jsonify({"code": 404, "message": "Post not found."}), 404

    data = request.get_json()
    user_id = data.get("user_id")
    comment_id = data.get("comment_id")
    content = data.get("content")

    comment = Comments(
        post_id=post_id, comment_id=comment_id, content=content, user_id=user_id
    )

    try:
        db.session.add(comment)
        post.replies += 1
        db.session.commit()
        return jsonify({"code": 201, "data": comment.json()}), 201
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred creating the comment: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/v1/getComments/<uuid:post_id>")
def getComments(post_id):
    comments = (
        Comments.query.filter_by(post_id=post_id).order_by(Comments.created_at).all()
    )

    if comments:
        comments_data = [comment.json() for comment in comments]
        return jsonify({"code": 200, "data": comments_data}), 200
    else:
        return jsonify({"code": 404, "message": "No comments found for the post."}), 404


@app.route("/api/v1/updateComment/<string:comment_id>", methods=["PUT"])
def updateComment(comment_id):
    comment = Comments.query.get(comment_id)

    if not comment:
        return jsonify({"code": 404, "message": "Comment not found."}), 404

    data = request.get_json()
    content = data.get("content")

    comment.content = content

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": comment.json()}), 200
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred updating the comment: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/v1/deleteComment/<string:comment_id>", methods=["DELETE"])
def deleteComment(comment_id):
    comment = Comments.query.get(comment_id)

    if not comment:
        return jsonify({"code": 404, "message": "Comment not found."}), 404

    try:
        post = Posts.query.get(comment.post_id)
        post.replies -= 1
        db.session.delete(comment)
        db.session.commit()
        return jsonify({"code": 200, "message": "Comment deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred deleting the comment: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/v1/addForum", methods=["POST"])
def create_forum():
    data = request.get_json()
    concert_id = data.get("concert_id")
    concert_name = data.get("concert_name")
    user_id = data.get("user_id")

    new_forum = Forums(
        concert_id=concert_id, concert_name=concert_name, user_id=user_id
    )

    try:
        db.session.add(new_forum)
        db.session.commit()
        return jsonify({"code": 201, "data": new_forum.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/api/v1/getForums", methods=["GET"])
def get_forums():
    forums = Forums.query.all()
    forum_list = [forum.json() for forum in forums]
    return jsonify({"code": 200, "data": forum_list}), 200


@app.route("/api/v1/getForum/<string:user_id>", methods=["GET"])
def get_forum_by_userId(user_id):
    filtered_forums = Forums.query.filter(Forums.user_id == user_id).all()

    print(filtered_forums)
    filtered_forums_json = [forum.json() for forum in filtered_forums]
    print(filtered_forums_json)
    if filtered_forums:
        return jsonify({"code": 200, "data": filtered_forums_json}), 200
    else:
        return jsonify({"code": 404, "message": "Forum not found."}), 404


@app.route("/api/v1/getForumByConcertID/<string:concert_id>", methods=["GET"])
def get_forum(concert_id):
    forum = Forums.query.get(concert_id)
    if forum:
        return jsonify({"code": 200, "data": forum.json()}), 200
    else:
        return jsonify({"code": 404, "message": "Forum not found."}), 404


@app.route("/api/v1/updateForum/<string:concert_id>", methods=["PUT"])
def update_forum(concert_id):
    forum = Forums.query.get(concert_id)
    if not forum:
        return jsonify({"code": 404, "message": "Forum not found."}), 404

    data = request.get_json()
    forum.concert_id = data.get("concert_id", forum.concert_id)

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": forum.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"An error occurred: {str(e)}"}), 500


@app.route("/api/v1/deleteForum/<string:concert_id>", methods=["DELETE"])
def delete_forum(concert_id):
    forum = Forums.query.get(concert_id)
    if not forum:
        return jsonify({"code": 404, "message": "Forum not found."}), 404

    try:
        db.session.delete(forum)
        db.session.commit()
        return jsonify({"code": 200, "message": "Forum deleted successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
