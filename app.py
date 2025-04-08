import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "super-secret-key"  # Needed for sessions, etc.

# If you do NOT want to use a DB at all, you can skip everything related to db/SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookmarks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Bookmark user={self.user_id}, item_id={self.item_id}, item_type={self.item_type}>"

with app.app_context():
    db.create_all()


#############
# HELPER
#############
def get_current_user_id():
    # For a real app, you'd have a proper auth system.
    # For now, store a "user_id" in session or just default to 'guest'.
    return session.get("user_id", "guest")


#############
# LOAD JSON
#############
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# For example, we have "newsletter.json" (like your front-page news)
newsletter_data = []
newsletter_file = os.path.join(DATA_DIR, "newsletter.json")
if os.path.exists(newsletter_file):
    with open(newsletter_file, "r", encoding="utf-8") as f:
        newsletter_data = json.load(f)

# For example, "radioPlay.json" for music
music_data = {}
radio_file = os.path.join(DATA_DIR, "radioPlay.json")
if os.path.exists(radio_file):
    with open(radio_file, "r", encoding="utf-8") as f:
        music_data = json.load(f)
else:
    music_data = {"songs": []}


#############
# ROUTES
#############
@app.route("/")
def home():
    # For simplicity, show "news" as the home page
    return redirect(url_for("news"))

@app.route("/news")
def news():
    # Example usage: display newsletter data
    # Sort by date descending if you wish
    sorted_news = sorted(
        newsletter_data,
        key=lambda x: x.get("date", ""),
        reverse=True
    )
    return render_template("index.html", news_items=sorted_news)

@app.route("/media")
def media():
    return render_template("media.html")

@app.route("/music")
def music():
    # Pass the songs to the template
    all_songs = music_data.get("songs", [])
    return render_template("music.html", songs=all_songs)

@app.route("/podcast")
def podcast():
    return render_template("podcast.html")

@app.route("/about")
def about():
    return render_template("about.html")


#############
# BOOKMARK 
#############
@app.route("/bookmark", methods=["POST"])
def bookmark():
    """
    A minimal endpoint to bookmark an item (e.g. a song).
    We expect a form or JSON with item_id, item_type.
    """
    user_id = get_current_user_id()
    item_id = request.form.get("item_id")
    item_type = request.form.get("item_type", "music")

    if not item_id:
        return jsonify({"error": "No item_id provided"}), 400

    new_bm = Bookmark(user_id=user_id, item_id=item_id, item_type=item_type)
    db.session.add(new_bm)
    db.session.commit()
    return jsonify({"success": True, "item_id": item_id, "item_type": item_type})


@app.route("/my-bookmarks")
def my_bookmarks():
    user_id = get_current_user_id()
    results = Bookmark.query.filter_by(user_id=user_id).all()
    return render_template("bookmarks.html", bookmarks=results)


#############
# SITEMAP
#############
@app.route("/sitemap")
def sitemap():
    routes = []
    for rule in app.url_map.iter_rules():
        if "static" in rule.endpoint:
            continue
        routes.append({"endpoint": rule.endpoint, "methods": list(rule.methods), "url": str(rule)})
    return jsonify({"routes": routes})


if __name__ == "__main__":
    app.run(debug=True)