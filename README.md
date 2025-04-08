# Ahoy Indie Media

A platform for independent artists, musicians, and content creators to showcase their work.

## Features

- Music player with playlist support
- Video content streaming
- Podcast episodes
- News articles
- Bookmarking system
- Responsive design
- Search and filter functionality

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ahoy-indie-media.git
cd ahoy-indie-media
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```
Edit the `.env` file with your configuration.

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

The application will be available at `http://localhost:5000`.

## Deployment

This application is configured for deployment on Render.com. To deploy:

1. Create a new Web Service on Render.com
2. Connect your GitHub repository
3. Set the following environment variables:
   - `FLASK_APP=app.py`
   - `SECRET_KEY=your-secret-key-here`
   - `DATABASE_URL=your-database-url`

## Development

- Frontend: HTML, CSS, JavaScript
- Backend: Python, Flask
- Database: SQLite (development), PostgreSQL (production)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.