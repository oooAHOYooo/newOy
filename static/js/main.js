// Audio player functionality
let audioPlayer = null;
let currentSong = null;
let isPlaying = false;
let isInitialized = false;

// Initialize audio player
function initAudioPlayer() {
    if (isInitialized) return;
    
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
    
    // Initialize play/pause button
    const playPauseBtn = document.getElementById('play-pause-btn');
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', togglePlayPause);
    }
    
    // Initialize skip buttons
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    if (prevBtn) prevBtn.addEventListener('click', playPreviousSong);
    if (nextBtn) nextBtn.addEventListener('click', playNextSong);
    
    isInitialized = true;
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
    
    // Update sidebar now playing
    const sidebarTitle = document.getElementById('sidebar-song-title');
    const sidebarArtist = document.getElementById('sidebar-artist');
    const sidebarArt = document.getElementById('sidebar-album-art');
    const sidebarPlayBtn = document.querySelector('.sidebar-controls .play-btn i');
    const sidebarNowPlaying = document.querySelector('.sidebar-now-playing');
    
    if (sidebarTitle) sidebarTitle.textContent = currentSong.title;
    if (sidebarArtist) sidebarArtist.textContent = currentSong.artist;
    if (sidebarArt) sidebarArt.src = currentSong.albumArt;
    if (sidebarPlayBtn) {
        sidebarPlayBtn.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
    }
    if (sidebarNowPlaying) {
        sidebarNowPlaying.classList.add('active');
    }

    // Update progress
    updateProgress();

    // Sync with server
    fetch('/api/now-playing', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'music',
            title: currentSong.title,
            artist: currentSong.artist,
            albumArt: currentSong.albumArt,
            url: currentSong.url
        })
    }).catch(error => console.error('Error updating now playing:', error));
}

// Initialize now playing from server
function initNowPlaying() {
    fetch('/api/now-playing')
        .then(response => response.json())
        .then(data => {
            if (data.now_playing && data.now_playing.title) {
                const sidebarTitle = document.getElementById('sidebar-song-title');
                const sidebarArtist = document.getElementById('sidebar-artist');
                const sidebarArt = document.getElementById('sidebar-album-art');
                const sidebarPlayBtn = document.querySelector('.sidebar-controls button i');
                
                if (sidebarTitle) sidebarTitle.textContent = data.now_playing.title;
                if (sidebarArtist) sidebarArtist.textContent = data.now_playing.artist;
                if (sidebarArt) sidebarArt.src = data.now_playing.albumArt;
                if (sidebarPlayBtn) {
                    sidebarPlayBtn.className = 'fas fa-play';
                }

                // If it's a music item, update the main player too
                if (data.now_playing.type === 'music') {
                    currentSong = {
                        title: data.now_playing.title,
                        artist: data.now_playing.artist,
                        albumArt: data.now_playing.albumArt,
                        url: data.now_playing.url
                    };
                    updateNowPlaying();
                }
            }
        })
        .catch(error => console.error('Error loading now playing:', error));
}

// Update progress bar
function updateProgress() {
    if (!audioPlayer) return;
    
    const progressBar = document.querySelector('.sidebar-progress .progress');
    const currentTimeElement = document.getElementById('current-time');
    const totalTimeElement = document.getElementById('total-time');
    
    if (progressBar) {
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

// Format time in MM:SS
function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
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

// Play previous song
function playPreviousSong() {
    // Implement playlist functionality here
    console.log('Play previous song - implement playlist functionality');
}

// Play next song
function playNextSong() {
    // Implement playlist functionality here
    console.log('Play next song - implement playlist functionality');
    
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
    
    if (isPlaying) {
        audioPlayer.pause();
    } else {
        audioPlayer.play();
    }
    
    isPlaying = !isPlaying;
    updateNowPlaying();
}

// Update play/pause button
function updatePlayPauseButton() {
    const playPauseBtn = document.getElementById('play-pause-btn');
    if (playPauseBtn) {
        playPauseBtn.innerHTML = isPlaying ? 
            '<i class="fas fa-pause"></i>' : 
            '<i class="fas fa-play"></i>';
    }
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
    if (sidebar) {
        const isSidebarOpen = localStorage.getItem('sidebarOpen') === 'true';
        if (isSidebarOpen) {
            sidebar.classList.add('active');
            document.body.classList.add('sidebar-open');
        }
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Space bar to play/pause
        if (e.code === 'Space' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            togglePlayPause();
        }
        // Left arrow to previous song
        if (e.code === 'ArrowLeft' && e.altKey) {
            playPreviousSong();
        }
        // Right arrow to next song
        if (e.code === 'ArrowRight' && e.altKey) {
            playNextSong();
        }
        // Escape to close sidebar
        if (e.code === 'Escape') {
            const sidebar = document.querySelector('.left-dashboard');
            if (sidebar && sidebar.classList.contains('active')) {
                toggleSidebar();
            }
        }
    });
    
    // Initialize now playing from server
    initNowPlaying();
    
    // Add click handler for sidebar play button
    const sidebarPlayBtn = document.querySelector('.sidebar-controls button');
    if (sidebarPlayBtn) {
        sidebarPlayBtn.addEventListener('click', togglePlayPause);
    }
    
    // Add click handler for progress bar
    const progressBar = document.querySelector('.sidebar-progress .progress-bar');
    if (progressBar) {
        progressBar.addEventListener('click', function(e) {
            if (!audioPlayer) return;
            
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const percentage = x / rect.width;
            
            audioPlayer.currentTime = percentage * audioPlayer.duration;
            updateProgress();
        });
    }
    
    // Add timeupdate event listener for progress updates
    if (audioPlayer) {
        audioPlayer.addEventListener('timeupdate', updateProgress);
    }

    // --- Sidebar Like Button ---
    const likeBtn = document.getElementById('sidebar-like-btn');
    if (likeBtn) {
        likeBtn.addEventListener('click', function() {
            if (!currentSong || !currentSong.url) return;
            fetch('/bookmark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `item_id=${encodeURIComponent(currentSong.url)}&item_type=music`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const icon = likeBtn.querySelector('i');
                    icon.classList.toggle('fas');
                    icon.classList.toggle('far');
                    likeBtn.classList.toggle('active');
                }
            });
        });
    }

    // --- Sidebar Mute Button ---
    const muteBtn = document.getElementById('sidebar-mute-btn');
    if (muteBtn) {
        muteBtn.addEventListener('click', function() {
            if (!audioPlayer) return;
            audioPlayer.muted = !audioPlayer.muted;
            const icon = muteBtn.querySelector('i');
            if (audioPlayer.muted) {
                icon.classList.remove('fa-volume-mute');
                icon.classList.add('fa-volume-off');
            } else {
                icon.classList.remove('fa-volume-off');
                icon.classList.add('fa-volume-mute');
            }
        });
    }

    // --- Sidebar Prev/Next Buttons ---
    const prevBtn = document.getElementById('sidebar-prev-btn');
    const nextBtn = document.getElementById('sidebar-next-btn');
    if (prevBtn) prevBtn.addEventListener('click', playPreviousSong);
    if (nextBtn) nextBtn.addEventListener('click', playNextSong);
});

// --- Playlist Navigation ---
let playlist = [];
let playlistIndex = -1;

function setPlaylist(songs, startIndex) {
    playlist = songs;
    playlistIndex = startIndex;
}

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
    // Update playlist index if song is in playlist
    if (playlist.length > 0) {
        const idx = playlist.findIndex(s => s.url === songUrl);
        if (idx !== -1) playlistIndex = idx;
    }
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

function playPreviousSong() {
    if (playlist.length > 0 && playlistIndex > 0) {
        playlistIndex--;
        const song = playlist[playlistIndex];
        playSong(song.url, song.title, song.artist, song.albumArt);
    }
}

function playNextSong() {
    if (playlist.length > 0 && playlistIndex < playlist.length - 1) {
        playlistIndex++;
        const song = playlist[playlistIndex];
        playSong(song.url, song.title, song.artist, song.albumArt);
    }
} 