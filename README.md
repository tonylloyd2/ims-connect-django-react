# IMS Connect

A Django-React application for inventory management system.

## Project Structure
```
ims-connect-django-react/
├── backend/          # Django backend
│   ├── api/         # Django REST API
│   ├── core/        # Main Django app
│   └── manage.py    
├── frontend/        # React frontend
└── requirements.txt # Python dependencies
```

## Setup Instructions

### Backend Setup
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
cd backend
python manage.py migrate
```

4. Start the Django server:
```bash
python manage.py runserver
```

### Frontend Setup
1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start the React development server:
```bash
npm start
```

## Development
- Backend API runs on: http://localhost:8000
- Frontend runs on: http://localhost:3000
