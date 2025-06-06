# Tangent

Tangent is a professional networking tool that helps people discover the most relevant connections at large events, based on shared context, interests, and mutual connections.

## Features

- **Smart Matching**: AI-powered recommendations based on shared interests and context
- **Proximity-Based Groups**: Create or join groups based on location radius
- **Event Mode**: Pre-loaded groups for event organizers
- **Modern UI**: Clean, minimal interface optimized for professional events
- **Mobile-First Design**: Responsive interface for on-the-go networking

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
5. Run migrations:
   ```bash
   python mysite/manage.py migrate
   ```
6. Start the development server:
   ```bash
   python mysite/manage.py runserver
   ```
7. Visit http://127.0.0.1:8000 in your browser

## Usage

### For Event Attendees
1. Create an account or log in
2. Complete your profile with interests and current projects
3. Choose between proximity mode or event mode
4. Browse recommended connections
5. View shared context and conversation starters

### For Event Organizers
1. Contact us to set up your event
2. Provide attendee list or registration data
3. Customize the onboarding experience
4. Monitor networking activity during the event

## Tech Stack
- Django
- Channels for WebSocket support
- OpenAI for smart matching
- Modern CSS framework for responsive design
