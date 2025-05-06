from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Video
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/videos')
def admin_videos():
    videos = Video.query.order_by(Video.created_at.desc()).all()
    return render_template('admin/videos.html', videos=videos)

@admin_bp.route('/videos/create', methods=['GET', 'POST'])
def create_video():
    if request.method == 'POST':
        title = request.form.get('title')
        src = request.form.get('src')
        type = request.form.get('type')
        thumbnail = request.form.get('thumbnail')
        category = request.form.get('category')

        if not all([title, src, type, category]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('admin.create_video'))

        video = Video(
            title=title,
            src=src,
            type=type,
            thumbnail=thumbnail,
            category=category,
            created_at=datetime.utcnow()
        )

        db.session.add(video)
        db.session.commit()
        flash('Video created successfully', 'success')
        return redirect(url_for('admin.admin_videos'))

    return render_template('admin/video_form.html')

@admin_bp.route('/videos/<int:video_id>/edit', methods=['GET', 'POST'])
def edit_video(video_id):
    video = Video.query.get_or_404(video_id)
    
    if request.method == 'POST':
        video.title = request.form.get('title')
        video.src = request.form.get('src')
        video.type = request.form.get('type')
        video.thumbnail = request.form.get('thumbnail')
        video.category = request.form.get('category')

        if not all([video.title, video.src, video.type, video.category]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('admin.edit_video', video_id=video_id))

        db.session.commit()
        flash('Video updated successfully', 'success')
        return redirect(url_for('admin.admin_videos'))

    return render_template('admin/video_form.html', video=video)

@admin_bp.route('/videos/<int:video_id>/delete', methods=['POST'])
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    flash('Video deleted successfully', 'success')
    return redirect(url_for('admin.admin_videos')) 