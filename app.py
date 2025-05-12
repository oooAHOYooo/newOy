import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Change this in production

# If you do NOT want to use a DB at all, you can skip everything related to db/SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASE_URL', 'sqlite:///bookmarks.db')
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
newsletter_data = {"newsletters": []}
newsletter_file = os.path.join(DATA_DIR, "newsletter.json")
if os.path.exists(newsletter_file):
    with open(newsletter_file, "r", encoding="utf-8") as f:
        newsletter_data = json.load(f)

# For example, "radioPlay.json" for music
music_data = {"songs": []}
radio_file = os.path.join(DATA_DIR, "radioPlay.json")
if os.path.exists(radio_file):
    with open(radio_file, "r", encoding="utf-8") as f:
        music_data = json.load(f)

# Load marketplace data
marketplace_data = {"categories": [], "products": []}
marketplace_file = os.path.join(DATA_DIR, "marketplace.json")
if os.path.exists(marketplace_file):
    with open(marketplace_file, "r", encoding="utf-8") as f:
        marketplace_data = json.load(f)

# Load artist data
def load_artists():
    with open('data/artists.json', 'r') as f:
        return json.load(f)['artists']


#############
# ROUTES
#############
@app.route("/")
def home():
    # For simplicity, show "news" as the home page
    return redirect(url_for("news"))

@app.route("/news")
def news():
    try:
        # Get newsletters and format them for the template
        newsletters = newsletter_data.get("newsletters", [])
        categories = newsletter_data.get("categories", [])
        formatted_news = []
        
        for newsletter in newsletters:
            category_id = newsletter.get("categoryId", "")
            category_label = next((cat["label"] for cat in categories if cat["id"] == category_id), "")
            formatted_news.append({
                "title": newsletter.get("title", "Untitled"),
                "date": newsletter.get("date", ""),
                "content": newsletter.get("content", ""),
                "category": category_label,
                "tags": newsletter.get("tags", [])
            })
            
        # Sort by date, newest first
        sorted_news = sorted(
            formatted_news,
            key=lambda x: x.get("date", ""),
            reverse=True
        )
        
        return render_template("index.html", news_items=sorted_news)
    except Exception as e:
        app.logger.error(f"Error in news route: {str(e)}")
        return render_template("index.html", news_items=[], error="Failed to load news")

@app.route("/media")
def media():
    with open(os.path.join(DATA_DIR, "tv_channels.json"), "r", encoding="utf-8") as f:
        tv_data = json.load(f)
    return render_template("media.html", channels=tv_data["channels"])

@app.route("/music")
def music():
    try:
        all_songs = music_data.get("songs", [])
        return render_template("music.html", songs=all_songs)
    except Exception as e:
        app.logger.error(f"Error in music route: {str(e)}")
        return render_template("music.html", songs=[], error="Failed to load music")

@app.route("/podcast")
def podcast():
    return render_template("podcast.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/artists')
def artists():
    artists_data = load_artists()
    return render_template('artists.html', artists=artists_data)

@app.route('/artist/<artist_id>')
def artist_detail(artist_id):
    artists_data = load_artists()
    artist = next((a for a in artists_data if a['id'] == artist_id), None)
    if artist is None:
        return render_template('404.html'), 404
    return render_template('artist_detail.html', artist=artist)


#############
# BOOKMARK 
#############
@app.route("/bookmark", methods=["POST"])
def bookmark():
    """
    A minimal endpoint to bookmark an item (e.g. a song).
    We expect a form or JSON with item_id, item_type.
    """
    try:
        user_id = get_current_user_id()
        item_id = request.form.get("item_id")
        item_type = request.form.get("item_type", "music")

        if not item_id:
            return jsonify({"error": "No item_id provided"}), 400

        new_bm = Bookmark(user_id=user_id, item_id=item_id, item_type=item_type)
        db.session.add(new_bm)
        db.session.commit()
        return jsonify({"success": True, "item_id": item_id, "item_type": item_type})
    except Exception as e:
        app.logger.error(f"Error in bookmark route: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/my-bookmarks")
def my_bookmarks():
    try:
        user_id = get_current_user_id()
        results = Bookmark.query.filter_by(user_id=user_id).all()
        return render_template("bookmarks.html", bookmarks=results)
    except Exception as e:
        app.logger.error(f"Error in my_bookmarks route: {str(e)}")
        return render_template("bookmarks.html", bookmarks=[], error="Failed to load bookmarks")


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

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

#############
# MARKETPLACE ROUTES
#############
@app.route("/shop")
def marketplace_home():
    """Main marketplace page showing featured products and categories"""
    marketplace_data = {
        "categories": [
            {
                "name": "Music",
                "slug": "music",
                "subcategories": [
                    {"name": "Albums", "slug": "albums"},
                    {"name": "Singles", "slug": "singles"},
                    {"name": "Merchandise", "slug": "merch"}
                ]
            },
            {
                "name": "Media",
                "slug": "media",
                "subcategories": [
                    {"name": "Videos", "slug": "videos"},
                    {"name": "Photos", "slug": "photos"}
                ]
            }
        ],
        "products": [
            {
                "id": 1,
                "name": "Sample Product",
                "featured": True,
                "price": 9.99,
                "description": "A sample product"
            }
        ]
    }
    
    categories = marketplace_data.get("categories", [])
    featured_products = [p for p in marketplace_data.get("products", []) if p.get("featured")]
    return render_template(
        "marketplace/home.html",
        marketplace_data=marketplace_data,
        categories=categories,
        featured_products=featured_products
    )

@app.route("/shop/category/<string:category_slug>")
def category_view(category_slug):
    """Show products in a specific category"""
    categories = marketplace_data.get("categories", [])
    category = next((c for c in categories if c["slug"] == category_slug), None)
    
    if not category:
        return render_template("404.html"), 404
        
    # Get products for this category
    products = [p for p in marketplace_data.get("products", []) 
               if p["category_id"] == category["id"]]
               
    return render_template(
        "marketplace/category.html",
        category=category,
        products=products
    )

@app.route("/shop/category/<string:category_slug>/<string:subcategory_slug>")
def subcategory_view(category_slug, subcategory_slug):
    """Show products in a specific subcategory"""
    categories = marketplace_data.get("categories", [])
    category = next((c for c in categories if c["slug"] == category_slug), None)
    
    if not category:
        return render_template("404.html"), 404
        
    subcategory = next((s for s in category["subcategories"] 
                       if s["slug"] == subcategory_slug), None)
                       
    if not subcategory:
        return render_template("404.html"), 404
        
    # Get products for this subcategory
    products = [p for p in marketplace_data.get("products", []) 
               if p["subcategory_id"] == subcategory["id"]]
               
    return render_template(
        "marketplace/subcategory.html",
        category=category,
        subcategory=subcategory,
        products=products
    )

@app.route("/shop/product/<string:product_slug>")
def product_view(product_slug):
    """Show individual product details"""
    products = marketplace_data.get("products", [])
    product = next((p for p in products if p["slug"] == product_slug), None)
    
    if not product:
        return render_template("404.html"), 404
        
    # Get category and subcategory info
    category = next((c for c in marketplace_data["categories"] 
                    if c["id"] == product["category_id"]), None)
    subcategory = next((s for s in category["subcategories"] 
                       if s["id"] == product["subcategory_id"]), None)
                       
    # Get related products from same subcategory
    related_products = [p for p in products 
                       if p["subcategory_id"] == product["subcategory_id"] 
                       and p["id"] != product["id"]][:4]  # Show up to 4 related products
                       
    return render_template(
        "marketplace/product.html",
        product=product,
        category=category,
        subcategory=subcategory,
        related_products=related_products
    )

@app.route("/shop/cart", methods=["GET"])
def view_cart():
    """View shopping cart"""
    cart = session.get("cart", [])
    cart_items = []
    total = 0
    
    if cart:
        products = marketplace_data.get("products", [])
        for item in cart:
            product = next((p for p in products if p["id"] == item["product_id"]), None)
            if product:
                item_total = product["price"] * item["quantity"]
                cart_items.append({
                    "product": product,
                    "quantity": item["quantity"],
                    "total": item_total
                })
                total += item_total
                
    return render_template(
        "marketplace/cart.html",
        cart_items=cart_items,
        total=total
    )

@app.route("/shop/cart/add", methods=["POST"])
def add_to_cart():
    """Add item to shopping cart"""
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", 1, type=int)
    
    if not product_id:
        return jsonify({"error": "Product ID is required"}), 400
        
    # Validate product exists
    products = marketplace_data.get("products", [])
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
        
    # Initialize cart if needed
    if "cart" not in session:
        session["cart"] = []
        
    # Check if product already in cart
    cart = session["cart"]
    cart_item = next((item for item in cart if item["product_id"] == product_id), None)
    
    if cart_item:
        cart_item["quantity"] += quantity
    else:
        cart.append({"product_id": product_id, "quantity": quantity})
        
    session["cart"] = cart
    
    return jsonify({
        "message": "Product added to cart",
        "cart_count": len(cart)
    })

@app.route("/settings")
def settings():
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)