import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import random

class TerminalApp:
    def __init__(self):
        self.commands = {
            'help': self.show_help,
            'ls': self.list_content,
            'cat': self.show_content,
            'search': self.search_content,
            'stats': self.show_stats,
            'play': self.play_media,
            'bookmark': self.manage_bookmarks,
            'chat': self.start_chat,
            'clear': self.clear_screen,
            'exit': self.exit_app
        }
        
        self.data_dir = 'data'
        self.current_path = '/'
        self.history = []
        self.chat_mode = False
        self.chat_history = []
        self.questions_remaining = 20
        
        # Load all data
        self.load_data()
        
    def load_data(self):
        """Load all data files"""
        self.music = self._load_json('radioPlay.json')
        self.podcasts = self._load_json('podcasts.json')
        self.news = self._load_json('newsletter.json')
        self.artists = self._load_json('artists.json')
        self.marketplace = self._load_json('marketplace.json')
        
    def _load_json(self, filename: str) -> dict:
        """Load a JSON file from the data directory"""
        try:
            with open(os.path.join(self.data_dir, filename), 'r') as f:
                return json.load(f)
        except:
            return {}
            
    def execute_command(self, command: str) -> str:
        """Execute a terminal command"""
        if not command.strip():
            return ""
            
        self.history.append(command)
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd in self.commands:
            return self.commands[cmd](*args)
        else:
            return f"Command not found: {cmd}. Type 'help' for available commands."
            
    def show_help(self) -> str:
        """Show available commands"""
        help_text = """
Available commands:
  help                    Show this help message
  ls [path]              List content in current directory
  cat <file>             Show content of a file
  search <query>         Search across all content
  stats                  Show statistics about the content
  play <type> <id>       Play music, podcast, or video
  bookmark <add|list>    Manage bookmarks
  chat                   Start chat mode (20 questions)
  clear                  Clear the screen
  exit                   Exit the application
        """
        return help_text.strip()
        
    def list_content(self, path: str = '') -> str:
        """List content in the current directory"""
        if not path:
            path = self.current_path
            
        if path == '/':
            return """
Content types:
  /music     - Music library
  /podcasts  - Podcast episodes
  /news      - News articles
  /artists   - Artist profiles
  /shop      - Marketplace items
            """
            
        content = []
        if path == '/music':
            content = [f"{song['id']}: {song['title']} - {song['artist']}" 
                      for song in self.music.get('songs', [])]
        elif path == '/podcasts':
            content = [f"{podcast['id']}: {podcast['title']} - {podcast['host']}" 
                      for podcast in self.podcasts.get('podcasts', [])]
        elif path == '/news':
            content = [f"{article['id']}: {article['title']} ({article['date']})" 
                      for article in self.news.get('newsletters', [])]
        elif path == '/artists':
            content = [f"{artist['id']}: {artist['name']}" 
                      for artist in self.artists.get('artists', [])]
        elif path == '/shop':
            content = [f"{item['id']}: {item['name']} - ${item['price']}" 
                      for item in self.marketplace.get('products', [])]
                      
        return "\n".join(content) if content else "No content found"
        
    def show_content(self, file_id: str) -> str:
        """Show content of a specific file"""
        try:
            file_id = int(file_id)
        except:
            return "Invalid file ID"
            
        # Search across all content types
        for content_type in ['music', 'podcasts', 'news', 'artists', 'shop']:
            items = getattr(self, content_type).get(content_type, [])
            for item in items:
                if item.get('id') == file_id:
                    return json.dumps(item, indent=2)
                    
        return "File not found"
        
    def search_content(self, *query_parts) -> str:
        """Search across all content"""
        query = ' '.join(query_parts).lower()
        results = []
        
        # Search in music
        for song in self.music.get('songs', []):
            if (query in song['title'].lower() or 
                query in song['artist'].lower() or 
                query in song.get('album', '').lower()):
                results.append(f"Music: {song['title']} - {song['artist']}")
                
        # Search in podcasts
        for podcast in self.podcasts.get('podcasts', []):
            if (query in podcast['title'].lower() or 
                query in podcast['host'].lower()):
                results.append(f"Podcast: {podcast['title']} - {podcast['host']}")
                
        # Search in news
        for article in self.news.get('newsletters', []):
            if (query in article['title'].lower() or 
                query in article.get('content', '').lower()):
                results.append(f"News: {article['title']} ({article['date']})")
                
        return "\n".join(results) if results else "No results found"
        
    def show_stats(self) -> str:
        """Show statistics about the content"""
        stats = {
            'Music': len(self.music.get('songs', [])),
            'Podcasts': len(self.podcasts.get('podcasts', [])),
            'News Articles': len(self.news.get('newsletters', [])),
            'Artists': len(self.artists.get('artists', [])),
            'Shop Items': len(self.marketplace.get('products', []))
        }
        
        return "\n".join(f"{k}: {v} items" for k, v in stats.items())
        
    def play_media(self, media_type: str, media_id: str) -> str:
        """Play music, podcast, or video"""
        try:
            media_id = int(media_id)
        except:
            return "Invalid media ID"
            
        if media_type == 'music':
            for song in self.music.get('songs', []):
                if song['id'] == media_id:
                    return f"Playing: {song['title']} - {song['artist']}"
        elif media_type == 'podcast':
            for podcast in self.podcasts.get('podcasts', []):
                if podcast['id'] == media_id:
                    return f"Playing: {podcast['title']} - {podcast['host']}"
                    
        return "Media not found"
        
    def manage_bookmarks(self, action: str = 'list') -> str:
        """Manage bookmarks"""
        if action == 'list':
            # In a real app, this would load from a database
            return "No bookmarks found"
        elif action == 'add':
            return "Bookmark added"
        else:
            return "Invalid bookmark action"
            
    def start_chat(self) -> str:
        """Start chat mode with 20 questions logic"""
        self.chat_mode = True
        self.questions_remaining = 20
        self.chat_history = []
        
        return """
Chat mode activated! You have 20 questions remaining.
Type 'exit' to end chat mode.
What would you like to know about indie media?
        """
        
    def handle_chat(self, message: str) -> str:
        """Handle chat messages"""
        if not self.chat_mode:
            return "Chat mode not active. Type 'chat' to start."
            
        if message.lower() == 'exit':
            self.chat_mode = False
            return "Chat mode ended."
            
        if self.questions_remaining <= 0:
            self.chat_mode = False
            return "You've used all your questions. Chat mode ended."
            
        self.questions_remaining -= 1
        self.chat_history.append(('user', message))
        
        # Simple response generation based on keywords
        response = self._generate_response(message)
        self.chat_history.append(('assistant', response))
        
        return f"{response}\nQuestions remaining: {self.questions_remaining}"
        
    def _generate_response(self, message: str) -> str:
        """Generate a response based on the message"""
        message = message.lower()
        
        # Check for music-related queries
        if any(word in message for word in ['music', 'song', 'artist', 'album']):
            return self._get_music_response(message)
            
        # Check for podcast-related queries
        if any(word in message for word in ['podcast', 'episode', 'host']):
            return self._get_podcast_response(message)
            
        # Check for news-related queries
        if any(word in message for word in ['news', 'article', 'latest']):
            return self._get_news_response(message)
            
        # Default response
        return "I'm not sure about that. Could you rephrase your question?"
        
    def _get_music_response(self, message: str) -> str:
        """Generate music-related response"""
        songs = self.music.get('songs', [])
        if not songs:
            return "No music data available."
            
        if 'latest' in message:
            latest = max(songs, key=lambda x: x.get('date', ''))
            return f"The latest song is '{latest['title']}' by {latest['artist']}"
            
        if 'popular' in message:
            popular = random.choice(songs)
            return f"'{popular['title']}' by {popular['artist']} is quite popular"
            
        return f"I found {len(songs)} songs in the library. What specific information are you looking for?"
        
    def _get_podcast_response(self, message: str) -> str:
        """Generate podcast-related response"""
        podcasts = self.podcasts.get('podcasts', [])
        if not podcasts:
            return "No podcast data available."
            
        if 'latest' in message:
            latest = max(podcasts, key=lambda x: x.get('date', ''))
            return f"The latest podcast is '{latest['title']}' hosted by {latest['host']}"
            
        return f"I found {len(podcasts)} podcast episodes. What would you like to know about them?"
        
    def _get_news_response(self, message: str) -> str:
        """Generate news-related response"""
        articles = self.news.get('newsletters', [])
        if not articles:
            return "No news data available."
            
        if 'latest' in message:
            latest = max(articles, key=lambda x: x.get('date', ''))
            return f"The latest news is '{latest['title']}' from {latest['date']}"
            
        return f"I found {len(articles)} news articles. What specific information are you looking for?"
        
    def clear_screen(self) -> str:
        """Clear the screen"""
        return "\n" * 100  # In a real terminal, this would clear the screen
        
    def exit_app(self) -> str:
        """Exit the application"""
        return "Goodbye!" 