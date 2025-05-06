import os
import json
import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from routes.admin import admin_bp  # Import the admin blueprint
from models import db, User, Video, Bookmark, DailyContent  # Import all models from models.py
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///bookmarks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # Enable SQL query logging for debugging

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(admin_bp)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database
with app.app_context():
    db.create_all()
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin')  # Change this in production!
        db.session.add(admin)
        db.session.commit()

#############
# UTILITY FUNCTIONS
#############
def get_or_create_user(user_id):
    """Get existing user or create a new one"""
    user = User.query.filter_by(id=user_id).first()
    if not user:
        user = User(id=user_id, username=f"user_{user_id}", email=f"user_{user_id}@example.com")
        db.session.add(user)
        db.session.commit()
    return user

def handle_database_error(e):
    """Handle database-related errors"""
    db.session.rollback()
    app.logger.error(f"Database error: {str(e)}")
    return jsonify({"error": "Database operation failed"}), 500

def assign_daily_content():
    """Assign one piece of daily content from pool if none exists for today."""
    today = datetime.utcnow().date()

    existing = DailyContent.query.filter_by(publish_date=today).first()
    if existing:
        return existing

    # Get content that hasn't been assigned a date yet
    used_ids = [c.id for c in DailyContent.query.with_entities(DailyContent.id).filter(DailyContent.publish_date != None).all()]
    candidates = DailyContent.query.filter(~DailyContent.id.in_(used_ids)).all()

    # Fallback if everything's been used
    if not candidates:
        candidates = DailyContent.query.all()

    if not candidates:
        return None

    selected = random.choice(candidates)
    selected.publish_date = today
    db.session.commit()
    return selected

#############
# HELPER
#############
def get_current_user_id():
    # For a real app, you'd have a proper auth system.
    # For now, store a "user_id" in session or just default to 'guest'.
    return session.get("user_id", "guest")

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
        # For now, return an empty list of news items
        # In the future, you can implement a proper newsletter system
        return render_template("index.html", news_items=[])
    except Exception as e:
        app.logger.error(f"Error in news route: {str(e)}")
        return render_template("index.html", news_items=[], error="Failed to load news")

@app.route("/media")
def media():
    return render_template("media.html")

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

        # Get or create user
        user = get_or_create_user(user_id)
        
        # Create new bookmark
        new_bm = Bookmark(
            user_id=user_id,
            item_id=item_id,
            item_type=item_type
        )
        db.session.add(new_bm)
        db.session.commit()
        
        return jsonify({"success": True, "bookmark_id": new_bm.id})
    except Exception as e:
        return handle_database_error(e)

@app.route("/my-bookmarks")
def my_bookmarks():
    try:
        user_id = get_current_user_id()
        bookmarks = Bookmark.query.filter_by(user_id=user_id).all()
        return render_template("my_bookmarks.html", bookmarks=bookmarks)
    except Exception as e:
        return handle_database_error(e)

@app.route("/sitemap")
def sitemap():
    return render_template("sitemap.html")

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    return render_template('500.html'), 500

@app.route("/shop")
def marketplace_home():
    return render_template("shop/index.html")

@app.route("/shop/category/<string:category_slug>")
def category_view(category_slug):
    return render_template("shop/category.html", category_slug=category_slug)

@app.route("/shop/category/<string:category_slug>/<string:subcategory_slug>")
def subcategory_view(category_slug, subcategory_slug):
    return render_template("shop/subcategory.html", 
                         category_slug=category_slug, 
                         subcategory_slug=subcategory_slug)

@app.route("/shop/product/<string:product_slug>")
def product_view(product_slug):
    return render_template("shop/product.html", product_slug=product_slug)

@app.route("/shop/cart", methods=["GET"])
def view_cart():
    return render_template("shop/cart.html")

@app.route("/shop/cart/add", methods=["POST"])
def add_to_cart():
    try:
        product_id = request.form.get("product_id")
        quantity = int(request.form.get("quantity", 1))
        
        if not product_id:
            return jsonify({"error": "No product_id provided"}), 400
            
        # Here you would typically:
        # 1. Validate the product exists
        # 2. Check stock
        # 3. Add to session cart or database cart
        # 4. Return success
        
        return jsonify({
            "success": True,
            "message": "Item added to cart",
            "product_id": product_id,
            "quantity": quantity
        })
    except Exception as e:
        app.logger.error(f"Error adding to cart: {str(e)}")
        return jsonify({"error": "Failed to add item to cart"}), 500

@app.route("/videos")
def videos():
    try:
        videos = Video.query.all()
        return render_template("videos.html", videos=videos)
    except Exception as e:
        app.logger.error(f"Error in videos route: {str(e)}")
        return render_template("videos.html", videos=[], error="Failed to load videos")

@app.route("/videos/<category>")
def video_category(category):
    try:
        videos = Video.query.filter_by(category=category).all()
        return render_template("videos.html", videos=videos, category=category)
    except Exception as e:
        app.logger.error(f"Error in video_category route: {str(e)}")
        return render_template("videos.html", videos=[], category=category, error="Failed to load videos")

@app.route("/video/<int:video_id>")
def video_detail(video_id):
    try:
        video = Video.query.get(video_id)
        if not video:
            return render_template("404.html"), 404
        return render_template("video_detail.html", video=video)
    except Exception as e:
        app.logger.error(f"Error in video_detail route: {str(e)}")
        return render_template("404.html"), 404

@app.route("/api/videos")
def api_videos():
    try:
        videos = Video.query.all()
        return jsonify([{
            "id": video.id,
            "title": video.title,
            "src": video.src,
            "type": video.type,
            "thumbnail": video.thumbnail,
            "category": video.category,
            "created_at": video.created_at.isoformat(),
            "updated_at": video.updated_at.isoformat()
        } for video in videos])
    except Exception as e:
        app.logger.error(f"Error in api_videos route: {str(e)}")
        return jsonify({"error": "Failed to load videos"}), 500

@app.route("/api/videos/<category>")
def api_video_category(category):
    try:
        videos = Video.query.filter_by(category=category).all()
        return jsonify([{
            "id": video.id,
            "title": video.title,
            "src": video.src,
            "type": video.type,
            "thumbnail": video.thumbnail,
            "category": video.category,
            "created_at": video.created_at.isoformat(),
            "updated_at": video.updated_at.isoformat()
        } for video in videos])
    except Exception as e:
        app.logger.error(f"Error in api_video_category route: {str(e)}")
        return jsonify({"error": "Failed to load videos"}), 500

@app.route("/api/video/<int:video_id>")
def api_video_detail(video_id):
    try:
        video = Video.query.get(video_id)
        if not video:
            return jsonify({"error": "Video not found"}), 404
        return jsonify({
            "id": video.id,
            "title": video.title,
            "src": video.src,
            "type": video.type,
            "thumbnail": video.thumbnail,
            "category": video.category,
            "created_at": video.created_at.isoformat(),
            "updated_at": video.updated_at.isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error in api_video_detail route: {str(e)}")
        return jsonify({"error": "Failed to load video"}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated.', 'danger')
                return redirect(url_for('login'))
                
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('admin_dashboard')
            return redirect(next_page)
            
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
        
    videos = Video.query.all()
    users = User.query.all()
    return render_template('admin/dashboard.html', 
                         videos=videos, 
                         users=users,
                         current_user=current_user)

@app.route('/admin/videos')
@login_required
def admin_videos():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
        
    videos = Video.query.all()
    return render_template('admin/videos.html', videos=videos)

@app.route('/admin/videos/add', methods=['POST'])
@login_required
def add_video():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        url = request.form.get('url')
        thumbnail = request.form.get('thumbnail')
        category = request.form.get('category', 'general')
        
        if not all([title, url]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        video = Video(
            title=title,
            description=description,
            src=url,
            thumbnail=thumbnail,
            category=category
        )
        
        db.session.add(video)
        db.session.commit()
        
        return jsonify({'success': True, 'video_id': video.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/videos/update', methods=['POST'])
@login_required
def update_video():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        video_id = request.form.get('video_id')
        video = Video.query.get_or_404(video_id)
        
        video.title = request.form.get('title', video.title)
        video.description = request.form.get('description', video.description)
        video.src = request.form.get('url', video.src)
        video.thumbnail = request.form.get('thumbnail', video.thumbnail)
        video.category = request.form.get('category', video.category)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/videos/delete', methods=['POST'])
@login_required
def delete_video():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        video_id = request.form.get('video_id')
        video = Video.query.get_or_404(video_id)
        
        db.session.delete(video)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/import-videos', methods=['POST'])
@login_required
def import_videos():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        # Clear existing videos
        Video.query.delete()
        
        # Add sample videos (you can replace this with your actual import logic)
        videos = [
            Video(
                title="Sample Video 1",
                description="This is a sample video",
                src="https://example.com/video1.mp4",
                thumbnail="https://example.com/thumb1.jpg",
                category="general"
            ),
            Video(
                title="Sample Video 2",
                description="Another sample video",
                src="https://example.com/video2.mp4",
                thumbnail="https://example.com/thumb2.jpg",
                category="tutorial"
            )
        ]
        
        db.session.bulk_save_objects(videos)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
        
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Add a route to create new users (admin only)
@app.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin', False) == 'on'
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('create_user'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('create_user'))
            
        user = User(
            username=username,
            email=email,
            is_admin=is_admin
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('User created successfully.', 'success')
        return redirect(url_for('admin_users'))
        
    return render_template('admin/create_user.html')

# Add a route to edit users (admin only)
@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.is_admin = request.form.get('is_admin', False) == 'on'
        user.is_active = request.form.get('is_active', False) == 'on'
        
        new_password = request.form.get('password')
        if new_password:
            user.set_password(new_password)
            
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin_users'))
        
    return render_template('admin/edit_user.html', user=user)

# Add a route to delete users (admin only)
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
        
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin_users'))
        
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

#############
# DAILY CONTENT ROUTES
#############
@app.route('/daily-splash')
def daily_splash():
    try:
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                content = DailyContent.query.filter_by(publish_date=target_date).first()
                if not content:
                    flash('No content found for that date. Showing latest instead.', 'info')
                    content = DailyContent.query.order_by(DailyContent.publish_date.desc()).first()
            except ValueError:
                flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
                return redirect(url_for('daily_splash'))
        else:
            content = assign_daily_content()
            target_date = datetime.utcnow().date()

        return render_template('daily_splash.html', content=content, selected_date=target_date)
    except Exception as e:
        app.logger.error(f"Error in daily_splash: {str(e)}")
        return render_template('daily_splash.html', error="Something went wrong.")

@app.route('/daily-splash/archive')
def daily_splash_archive():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        contents = DailyContent.query.order_by(DailyContent.publish_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        return render_template('daily_splash_archive.html', contents=contents)
    except Exception as e:
        app.logger.error(f"Error in daily splash archive route: {str(e)}")
        return render_template('daily_splash_archive.html', error="Failed to load archive")

@app.route('/admin/daily-splash')
@login_required
def admin_daily_splash():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))
    try:
        contents = DailyContent.query.order_by(DailyContent.publish_date.desc()).all()
        return render_template('admin/daily_splash.html', contents=contents)
    except Exception as e:
        app.logger.error(f"Error in admin daily splash route: {str(e)}")
        return render_template('admin/daily_splash.html', error="Failed to load content")

@app.route('/admin/daily-splash/add', methods=['GET', 'POST'])
@login_required
def add_daily_splash():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            content_type = request.form.get('content_type')
            media_url = request.form.get('media_url')
            publish_date = datetime.strptime(request.form.get('publish_date'), '%Y-%m-%d').date()
            
            # Check if content already exists for this date
            existing_content = DailyContent.query.filter_by(publish_date=publish_date).first()
            if existing_content:
                flash('Content already exists for this date. Please choose a different date or edit the existing content.', 'error')
                return redirect(url_for('add_daily_splash'))
            
            new_content = DailyContent(
                title=title,
                content=content,
                content_type=content_type,
                media_url=media_url,
                publish_date=publish_date,
                author_id=current_user.id
            )
            
            db.session.add(new_content)
            db.session.commit()
            flash('Daily content added successfully!', 'success')
            return redirect(url_for('admin_daily_splash'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding daily content: {str(e)}")
            flash('Failed to add daily content.', 'error')
    
    # Pass today's date for the default value in the form
    return render_template('admin/add_daily_splash.html', today=datetime.utcnow().date())

@app.route('/admin/daily-splash/<int:content_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_daily_splash(content_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))
    
    content = DailyContent.query.get_or_404(content_id)
    
    if request.method == 'POST':
        try:
            new_publish_date = datetime.strptime(request.form.get('publish_date'), '%Y-%m-%d').date()
            
            # Check if content already exists for the new date (excluding current content)
            if new_publish_date != content.publish_date:
                existing_content = DailyContent.query.filter_by(publish_date=new_publish_date).first()
                if existing_content:
                    flash('Content already exists for this date. Please choose a different date.', 'error')
                    return redirect(url_for('edit_daily_splash', content_id=content_id))
            
            content.title = request.form.get('title')
            content.content = request.form.get('content')
            content.content_type = request.form.get('content_type')
            content.media_url = request.form.get('media_url')
            content.publish_date = new_publish_date
            
            db.session.commit()
            flash('Daily content updated successfully!', 'success')
            return redirect(url_for('admin_daily_splash'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating daily content: {str(e)}")
            flash('Failed to update daily content.', 'error')
    
    return render_template('admin/edit_daily_splash.html', content=content)

@app.route('/admin/daily-splash/<int:content_id>/delete', methods=['POST'])
@login_required
def delete_daily_splash(content_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('home'))
    
    try:
        content = DailyContent.query.get_or_404(content_id)
        db.session.delete(content)
        db.session.commit()
        flash('Daily content deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting daily content: {str(e)}")
        flash('Failed to delete daily content.', 'error')
    
    return redirect(url_for('admin_daily_splash'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)