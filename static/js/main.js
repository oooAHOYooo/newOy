// Audio player functionality
let audioPlayer = null;
let currentSong = null;
let isPlaying = false;

// Initialize audio player
function initAudioPlayer() {
    audioPlayer = new Audio();
    
    // Event listeners for audio player
    audioPlayer.addEventListener('timeupdate', updateProgress);
    audioPlayer.addEventListener('ended', playNextSong);
    audioPlayer.addEventListener('error', handlePlayerError);
    
    // Initialize progress bar
    const progressBar = document.querySelector('.progress');
    if (progressBar) {
        progressBar.addEventListener('click', seek);
    }
}

// Play song function
function playSong(songUrl, songTitle, artist, albumArt) {
    if (!audioPlayer) {
        initAudioPlayer();
    }
    
    currentSong = {
        url: songUrl,
        title: songTitle,
        artist: artist,
        albumArt: albumArt
    };
    
    audioPlayer.src = songUrl;
    audioPlayer.play()
        .then(() => {
            isPlaying = true;
            updateNowPlaying();
            updatePlayPauseButton();
        })
        .catch(error => {
            console.error('Error playing song:', error);
            handlePlayerError(error);
        });
}

// Update now playing widget
function updateNowPlaying() {
    if (!currentSong) return;
    
    const titleElement = document.getElementById('current-song-title');
    const artistElement = document.getElementById('current-artist');
    const albumArtElement = document.getElementById('current-album-art');
    const musicPlayer = document.querySelector('.music-player');
    const albumArt = document.querySelector('.album-art');
    
    if (titleElement) titleElement.textContent = currentSong.title;
    if (artistElement) artistElement.textContent = currentSong.artist;
    if (albumArtElement) albumArtElement.src = currentSong.albumArt;
    
    // Add active and playing states
    if (musicPlayer) {
        musicPlayer.classList.add('active', 'playing');
        // Reset fade timer when song changes
        resetFadeTimer();
    }
    if (albumArt) {
        albumArt.classList.add('glow-playing');
    }
}

// Update progress bar
function updateProgress() {
    const progressBar = document.querySelector('.progress');
    const currentTimeElement = document.getElementById('current-time');
    const totalTimeElement = document.getElementById('total-time');
    
    if (progressBar && audioPlayer) {
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        progressBar.style.width = `${progress}%`;
    }
    
    if (currentTimeElement) {
        currentTimeElement.textContent = formatTime(audioPlayer.currentTime);
    }
    
    if (totalTimeElement) {
        totalTimeElement.textContent = formatTime(audioPlayer.duration);
    }
}

// Format time (mm:ss)
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Seek in audio
function seek(e) {
    const progressBar = e.currentTarget;
    const rect = progressBar.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    
    if (audioPlayer) {
        audioPlayer.currentTime = percentage * audioPlayer.duration;
    }
}

// Play next song
function playNextSong() {
    // Implement playlist functionality here
    console.log('Song ended, implement playlist functionality');
    
    // Remove active states when song ends
    const musicPlayer = document.querySelector('.music-player');
    const albumArt = document.querySelector('.album-art');
    
    if (musicPlayer) {
        musicPlayer.classList.remove('active', 'playing');
    }
    if (albumArt) {
        albumArt.classList.remove('glow-playing');
    }
}

// Handle player errors
function handlePlayerError(error) {
    console.error('Audio player error:', error);
    const nowPlayingWidget = document.getElementById('now-playing-widget');
    const musicPlayer = document.querySelector('.music-player');
    const albumArt = document.querySelector('.album-art');
    
    if (nowPlayingWidget) {
        nowPlayingWidget.classList.add('error');
    }
    if (musicPlayer) {
        musicPlayer.classList.remove('active', 'playing');
    }
    if (albumArt) {
        albumArt.classList.remove('glow-playing');
    }
}

// Toggle play/pause
function togglePlayPause() {
    if (!audioPlayer) return;
    
    const musicPlayer = document.querySelector('.music-player');
    const albumArt = document.querySelector('.album-art');
    
    if (isPlaying) {
        audioPlayer.pause();
        if (musicPlayer) {
            musicPlayer.classList.remove('playing');
            // Start fade timer when paused
            resetFadeTimer();
        }
        if (albumArt) albumArt.classList.remove('glow-playing');
    } else {
        audioPlayer.play();
        if (musicPlayer) {
            musicPlayer.classList.add('playing');
            // Reset fade timer when playing
            resetFadeTimer();
        }
        if (albumArt) albumArt.classList.add('glow-playing');
    }
    
    isPlaying = !isPlaying;
    updatePlayPauseButton();
}

// Update play/pause button
function updatePlayPauseButton() {
    const playPauseBtn = document.getElementById('play-pause-btn');
    if (playPauseBtn) {
        playPauseBtn.innerHTML = isPlaying ? '<i class="fas fa-pause"></i>' : '<i class="fas fa-play"></i>';
    }
}

// Skip forward/backward
function skip(seconds) {
    if (!audioPlayer) return;
    
    audioPlayer.currentTime += seconds;
}

// Enhanced Sidebar functionality
function toggleSidebar() {
    const sidebar = document.querySelector('.left-dashboard');
    const mainContent = document.querySelector('.main-content');
    const toggleBtn = document.querySelector('.toggle-sidebar-btn');
    
    if (sidebar && mainContent && toggleBtn) {
        const isOpen = sidebar.classList.toggle('active');
        mainContent.classList.toggle('expanded');
        toggleBtn.classList.toggle('active');
        
        // Save state to localStorage
        localStorage.setItem('sidebarOpen', isOpen);
        
        // Add/remove body class for overlay
        document.body.classList.toggle('sidebar-open', isOpen);
    }
}

// Close sidebar when clicking outside
function handleOutsideClick(e) {
    const sidebar = document.querySelector('.left-dashboard');
    const toggleBtn = document.querySelector('.toggle-sidebar-btn');
    
    if (sidebar && sidebar.classList.contains('active') && 
        !sidebar.contains(e.target) && 
        !toggleBtn.contains(e.target)) {
        toggleSidebar();
    }
}

// Close sidebar when clicking a nav link
function handleNavClick() {
    const sidebar = document.querySelector('.left-dashboard');
    if (sidebar && sidebar.classList.contains('active')) {
        toggleSidebar();
    }
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize audio player
    initAudioPlayer();
    
    // Initialize music player fade timer
    const musicPlayer = document.querySelector('.music-player');
    let fadeTimeoutId;
    
    function resetFadeTimer() {
        if (!musicPlayer) return;
        
        musicPlayer.classList.remove('dimmed');
        clearTimeout(fadeTimeoutId);
        fadeTimeoutId = setTimeout(() => {
            musicPlayer.classList.add('dimmed');
        }, 3000);
    }
    
    // Listen for any interaction inside the music player
    if (musicPlayer) {
        ['mousemove', 'touchstart', 'keydown'].forEach(evt => {
            musicPlayer.addEventListener(evt, resetFadeTimer);
        });
        
        // Also reset timer on player interactions
        const controls = musicPlayer.querySelectorAll('button');
        controls.forEach(button => {
            button.addEventListener('click', resetFadeTimer);
        });
        
        // Reset timer on progress bar interaction
        const progressBar = musicPlayer.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.addEventListener('click', resetFadeTimer);
        }
        
        // Initial start
        resetFadeTimer();
    }
    
    // Sidebar toggle
    const toggleBtn = document.querySelector('.toggle-sidebar-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleSidebar);
    }
    
    // Close sidebar when clicking outside
    document.addEventListener('click', handleOutsideClick);
    
    // Close sidebar when clicking nav links
    const navLinks = document.querySelectorAll('.nav-button');
    navLinks.forEach(link => {
        link.addEventListener('click', handleNavClick);
    });
    
    // Restore sidebar state from localStorage
    const sidebar = document.querySelector('.left-dashboard');
    if (sidebar && localStorage.getItem('sidebarOpen') === 'true') {
        toggleSidebar();
    }
    
    // Add touch support for mobile
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    }, false);
    
    document.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, false);
    
    function handleSwipe() {
        const sidebar = document.querySelector('.left-dashboard');
        if (!sidebar) return;
        
        const swipeThreshold = 100;
        const swipeDistance = touchEndX - touchStartX;
        
        if (Math.abs(swipeDistance) > swipeThreshold) {
            if (swipeDistance > 0 && !sidebar.classList.contains('active')) {
                // Swipe right - open sidebar
                toggleSidebar();
            } else if (swipeDistance < 0 && sidebar.classList.contains('active')) {
                // Swipe left - close sidebar
                toggleSidebar();
            }
        }
    }
    
    // Play/Pause button
    const playPauseBtn = document.getElementById('play-pause-btn');
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', togglePlayPause);
    }
    
    // Skip buttons
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => skip(-15));
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => skip(15));
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        switch(e.key) {
            case ' ':
                if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                    e.preventDefault();
                    togglePlayPause();
                }
                break;
            case 'ArrowLeft':
                skip(-15);
                break;
            case 'ArrowRight':
                skip(15);
                break;
            case 'Escape':
                // Close sidebar with Escape key
                const sidebar = document.querySelector('.left-dashboard');
                if (sidebar && sidebar.classList.contains('active')) {
                    toggleSidebar();
                }
                break;
        }
    });
}); 