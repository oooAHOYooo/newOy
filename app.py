import os
import json
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pathlib import Path
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from terminal_app import TerminalApp
import random

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Change this in production

#############
# DATABASE
#############
def get_db():
    """Get database connection"""
    db = sqlite3.connect('data/ahoy.db')
    db.row_factory = sqlite3.Row  # This enables column access by name
    return db

def init_db():
    """Initialize database with tables"""
    db = get_db()
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    db.close()

def init_app():
    """Initialize the application"""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Initialize database if it doesn't exist
    if not os.path.exists('data/ahoy.db'):
        init_db()

#############
# HELPER
#############
def get_current_user_id():
    # For a real app, you'd have a proper auth system.
    # For now, store a "user_id" in session or just default to 'guest'.
    return session.get("user_id", "guest")

def load_bookmarks():
    """Load bookmarks from JSON file"""
    bookmarks_file = os.path.join(DATA_DIR, "bookmarks.json")
    if os.path.exists(bookmarks_file):
        with open(bookmarks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"bookmarks": []}

def save_bookmarks(bookmarks):
    """Save bookmarks to JSON file"""
    bookmarks_file = os.path.join(DATA_DIR, "bookmarks.json")
    with open(bookmarks_file, "w", encoding="utf-8") as f:
        json.dump(bookmarks, f, indent=2)

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
    try:
        with open(os.path.join(DATA_DIR, "tv_channels.json"), "r", encoding="utf-8") as f:
            tv_data = json.load(f)
        return render_template(
            "media.html", 
            channels=tv_data["channels"], 
            now_playing=session.get("now_playing", {})
        )
    except Exception as e:
        app.logger.error(f"Error in media route: {str(e)}")
        return render_template(
            "media.html", 
            channels=[], 
            error=str(e), 
            now_playing={}
        )

@app.route("/music")
def music():
    try:
        # Load songs from radioPlay.json
        with open('data/temp/ogJson/radioPlay.json', 'r') as f:
            data = json.load(f)
            songs = data.get('songs', [])

            # Sort songs by featured and new status
            songs.sort(key=lambda x: (
                not x.get('featured', False),  # Featured songs first
                not x.get('new', False),       # Then new songs
                x.get('id', 0)                 # Then by ID
            ))

        # Calculate meta info
        song_count = len(songs)
        artist_count = len(set(song.get('artist') for song in songs if song.get('artist')))
        last_updated = data.get('last_updated')
        if not last_updated:
            # Fallback: use file modified time
            import os
            ts = os.path.getmtime('data/temp/ogJson/radioPlay.json')
            from datetime import datetime
            last_updated = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')

        return render_template(
            'music.html', 
            songs=songs, 
            now_playing=session.get("now_playing", {}),
            song_count=song_count,
            artist_count=artist_count,
            last_updated=last_updated
        )
    except Exception as e:
        app.logger.error(f"Error in music route: {str(e)}")
        return render_template(
            'music.html', 
            error=str(e), 
            now_playing={},
            song_count=0,
            artist_count=0,
            last_updated='N/A'
        )

@app.route("/podcast")
def podcast():
    try:
        # Load podcast data
        with open(os.path.join(DATA_DIR, "podcasts.json"), "r", encoding="utf-8") as f:
            podcast_data = json.load(f)
        return render_template(
            "podcast.html", 
            podcasts=podcast_data.get("podcasts", []), 
            now_playing=session.get("now_playing", {})
        )
    except Exception as e:
        app.logger.error(f"Error in podcast route: {str(e)}")
        return render_template(
            "podcast.html", 
            podcasts=[], 
            error=str(e), 
            now_playing={}
        )

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

@app.route('/discover')
def discover():
    try:
        # Load songs from radioPlay.json
        with open('data/radioPlay.json', 'r') as f:
            songs = json.load(f)
        
        # Sort songs by featured status, new status, and ID
        songs.sort(key=lambda x: (
            not x.get('featured', False),  # Featured songs first
            not x.get('new', False),       # New songs second
            -x.get('id', 0)                # Then by ID (newest first)
        ))
        
        return render_template('discover.html', songs=songs)
    except Exception as e:
        print(f"Error loading discover page: {str(e)}")
        return render_template('discover.html', songs=[])

#############
# BOOKMARK 
#############
@app.route("/bookmark", methods=["POST"])
def bookmark():
    """Add or remove a bookmark"""
    try:
        item_id = request.form.get('item_id')
        item_type = request.form.get('item_type', 'music')  # Default to music type
        user_id = get_current_user_id()
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if bookmark exists
        existing = cursor.execute(
            'SELECT id FROM bookmarks WHERE user_id = ? AND item_id = ? AND item_type = ?',
            (user_id, item_id, item_type)
        ).fetchone()
        
        if existing:
            # Remove bookmark
            cursor.execute(
                'DELETE FROM bookmarks WHERE user_id = ? AND item_id = ? AND item_type = ?',
                (user_id, item_id, item_type)
            )
            action = 'removed'
        else:
            # Add bookmark
            cursor.execute(
                'INSERT INTO bookmarks (user_id, item_id, item_type, created_at) VALUES (?, ?, ?, ?)',
                (user_id, item_id, item_type, datetime.now())
            )
            action = 'added'
            
        db.commit()
        db.close()
        
        return jsonify({
            'success': True,
            'action': action,
            'message': f'Bookmark {action} successfully'
        })
    except Exception as e:
        app.logger.error(f"Error in bookmark route: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route("/my-bookmarks")
def my_bookmarks():
    try:
        user_id = get_current_user_id()
        db = get_db()
        
        # Get all bookmarks with their details
        bookmarks = db.execute('''
            SELECT b.*, 
                   CASE 
                       WHEN b.item_type = 'music' THEN m.songTitle
                       WHEN b.item_type = 'news' THEN n.title
                       ELSE NULL 
                   END as title,
                   CASE 
                       WHEN b.item_type = 'music' THEN m.artist
                       WHEN b.item_type = 'news' THEN n.author
                       ELSE NULL 
                   END as author,
                   CASE 
                       WHEN b.item_type = 'music' THEN m.album
                       ELSE NULL 
                   END as album,
                   CASE 
                       WHEN b.item_type = 'music' THEN m.duration
                       ELSE NULL 
                   END as duration,
                   CASE 
                       WHEN b.item_type = 'music' THEN m.coverArt
                       WHEN b.item_type = 'news' THEN n.image
                       ELSE NULL 
                   END as image,
                   CASE 
                       WHEN b.item_type = 'music' THEN m.mp3url
                       ELSE NULL 
                   END as mp3url,
                   CASE 
                       WHEN b.item_type = 'music' THEN m.artistUrl
                       ELSE NULL 
                   END as artistUrl
            FROM bookmarks b
            LEFT JOIN music m ON b.item_type = 'music' AND b.item_id = m.id
            LEFT JOIN news n ON b.item_type = 'news' AND b.item_id = n.id
            WHERE b.user_id = ?
            ORDER BY b.created_at DESC
        ''', (user_id,)).fetchall()
        
        db.close()
        return render_template("bookmarks.html", bookmarks=bookmarks)
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

@app.route("/api/theme", methods=["GET", "POST"])
def handle_theme():
    if request.method == "POST":
        theme = request.json.get("theme", "default")
        session["theme"] = theme
        return jsonify({"success": True, "theme": theme})
    return jsonify({"theme": session.get("theme", "default")})

def get_random_media():
    """Get a random media item (music or podcast)"""
    try:
        # Load music data
        with open('data/radioPlay.json', 'r') as f:
            music_data = json.load(f)
            songs = music_data.get('songs', [])
        
        # Load podcast data
        with open('data/podcasts.json', 'r') as f:
            podcast_data = json.load(f)
            podcasts = podcast_data.get('podcasts', [])
        
        # Combine all media
        all_media = []
        
        # Add songs
        for song in songs:
            all_media.append({
                'type': 'music',
                'title': song.get('songTitle', ''),
                'artist': song.get('artist', ''),
                'albumArt': song.get('coverArt', ''),
                'url': song.get('mp3url', '')
            })
        
        # Add podcasts
        for podcast in podcasts:
            all_media.append({
                'type': 'podcast',
                'title': podcast.get('title', ''),
                'artist': podcast.get('host', ''),
                'albumArt': podcast.get('cover_art', ''),
                'url': podcast.get('mp3url', '')
            })
        
        # Return random media if available
        if all_media:
            return random.choice(all_media)
        return None
    except Exception as e:
        app.logger.error(f"Error getting random media: {str(e)}")
        return None

@app.route("/api/now-playing", methods=["GET", "POST"])
def handle_now_playing():
    """Handle now playing updates and retrieval"""
    if request.method == "POST":
        try:
            data = request.json
            session["now_playing"] = {
                "type": data.get("type", "music"),
                "title": data.get("title", ""),
                "artist": data.get("artist", ""),
                "albumArt": data.get("albumArt", ""),
                "url": data.get("url", ""),
                "timestamp": datetime.now().isoformat()
            }
            return jsonify({
                "success": True, 
                "now_playing": session["now_playing"]
            })
        except Exception as e:
            app.logger.error(f"Error updating now playing: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    # GET request - return current now playing state or random media
    current_playing = session.get("now_playing", {})
    if not current_playing:
        # If nothing is playing, get random media
        random_media = get_random_media()
        if random_media:
            session["now_playing"] = {
                "type": random_media["type"],
                "title": random_media["title"],
                "artist": random_media["artist"],
                "albumArt": random_media["albumArt"],
                "url": random_media["url"],
                "timestamp": datetime.now().isoformat()
            }
            current_playing = session["now_playing"]
    
    return jsonify({
        "success": True,
        "now_playing": current_playing
    })

@app.route("/api/llm-chat", methods=["POST"])
def handle_llm_chat():
    """Handle LLM chat interactions"""
    try:
        data = request.json
        user_message = data.get("message", "")
        
        # Store chat history in session if it doesn't exist
        if "chat_history" not in session:
            session["chat_history"] = []
            
        # Add user message to history
        session["chat_history"].append({
            "role": "user",
            "message": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate response based on message content
        response_message = generate_chat_response(user_message)
        
        response = {
            "role": "assistant",
            "message": response_message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add response to history
        session["chat_history"].append(response)
        
        return jsonify({
            "success": True,
            "response": response
        })
    except Exception as e:
        app.logger.error(f"Error in LLM chat: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def generate_chat_response(message):
    """Generate a response based on the user's message"""
    message = message.lower()
    
    # Check for media-related queries
    if any(word in message for word in ['play', 'music', 'song', 'podcast']):
        random_media = get_random_media()
        if random_media:
            return f"Playing {random_media['type']}: {random_media['title']} by {random_media['artist']}"
    
    # Check for help-related queries
    if 'help' in message:
        return "Available commands:\n- play: Play random media\n- help: Show this help message\n- exit: Exit chat mode"
    
    # Default response
    return f"I received your message: {message}"

#############
# CONTENT SCHEDULER
#############
scheduler = BackgroundScheduler()

def update_broadcast_content():
    """Update broadcast content based on time of day"""
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        time_slot = "morning"
    elif 12 <= current_hour < 18:
        time_slot = "afternoon"
    elif 18 <= current_hour < 22:
        time_slot = "evening"
    else:
        time_slot = "late_night"
    
    # Load and update broadcast content
    broadcast_file = os.path.join(DATA_DIR, "broadcast_schedule.json")
    if os.path.exists(broadcast_file):
        with open(broadcast_file, "r", encoding="utf-8") as f:
            schedule = json.load(f)
            if time_slot in schedule:
                # Update the current broadcast content
                with open(os.path.join(DATA_DIR, "current_broadcast.json"), "w") as f:
                    json.dump(schedule[time_slot], f)

def update_featured_content():
    """Update featured content periodically"""
    # Load all available content
    with open(os.path.join(DATA_DIR, "newsletter.json"), "r") as f:
        all_content = json.load(f)
    
    # Select featured content based on recency and engagement
    featured = []
    for item in all_content.get("newsletters", []):
        if item.get("active", False):
            featured.append(item)
    
    # Update featured content
    with open(os.path.join(DATA_DIR, "featured_content.json"), "w") as f:
        json.dump({"featured": featured[:5]}, f)

def update_playlist():
    """Update music playlist based on time and user preferences"""
    with open(os.path.join(DATA_DIR, "radioPlay.json"), "r") as f:
        all_songs = json.load(f)
    
    # Create time-based playlists
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        mood = "energetic"
    elif 12 <= current_hour < 18:
        mood = "focused"
    elif 18 <= current_hour < 22:
        mood = "relaxed"
    else:
        mood = "chill"
    
    # Filter songs by mood and update playlist
    playlist = [song for song in all_songs.get("songs", []) 
               if song.get("mood", "").lower() == mood]
    
    with open(os.path.join(DATA_DIR, "current_playlist.json"), "w") as f:
        json.dump({"songs": playlist}, f)

# Schedule content updates
scheduler.add_job(update_broadcast_content, CronTrigger(minute='0'))  # Every hour
scheduler.add_job(update_featured_content, CronTrigger(hour='*/4'))   # Every 4 hours
scheduler.add_job(update_playlist, CronTrigger(minute='*/30'))       # Every 30 minutes

# Start the scheduler
scheduler.start()

# Initialize the app
init_app()

# Initialize terminal app
terminal_app = TerminalApp()

@app.route("/terminal")
def terminal():
    """Terminal interface page"""
    return render_template("terminal.html")

@app.route("/api/terminal/init", methods=["POST"])
def init_terminal():
    """Initialize terminal session"""
    try:
        # In a real app, you might want to create a new instance per session
        return jsonify({
            "success": True,
            "app": "Terminal initialized"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/terminal/execute", methods=["POST"])
def execute_terminal_command():
    """Execute a terminal command"""
    try:
        data = request.json
        command = data.get("command", "")
        
        if not command:
            return jsonify({
                "success": False,
                "error": "No command provided"
            }), 400
            
        # Execute command using terminal app
        response = terminal_app.execute_command(command)
        
        return jsonify({
            "success": True,
            "response": response
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)