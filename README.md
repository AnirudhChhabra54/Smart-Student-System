# Student Dashboard System

A comprehensive AI-driven Student Dashboard System for educational institutions that streamlines academic management, automates marksheet scanning, provides performance predictions, and offers interactive features for enhanced learning.

## Features

- Automatic Marksheet Scanning & Data Extraction
- AI-Driven Performance Prediction
- Role-Based Access Control
- Multi-Institution Support
- Interactive Features:
  - AI-Based Timetable Constructor
  - Stopwatch & Time Tracking
  - Voice Assistant
  - Real-time Notifications
  - Attendance Monitoring
  - Collaboration Tools
  - Calendar Integration
  - Parental Portal
  - Gamification
  - Data Visualization

## Project Structure

```
.
├── backend/           # Flask backend API
│   ├── app.py        # Main application entry
│   ├── config.py     # Configuration settings
│   ├── routes.py     # API endpoints
│   ├── auth.py       # Authentication logic
│   ├── ocr.py        # OCR processing
│   ├── predict.py    # AI prediction models
│   └── utils.py      # Utility functions
│
└── frontend/         # React frontend application
    ├── public/      # Static files
    └── src/         # Source files
        ├── components/  # React components
        └── styles/     # CSS styles
```

## Setup Instructions

1. Backend Setup:
```bash
cd backend
pip install -r requirements.txt
python app.py
```

2. Frontend Setup:
```bash
cd frontend
npm install
npm start
```

## API Documentation

Detailed API documentation will be available at `/api/docs` when running the backend server.

## Technologies Used

- Backend: Python, Flask, PyTesseract (OCR), Machine Learning
- Frontend: React, Tailwind CSS
- Authentication: JWT
- Database: SQLite (Development) / PostgreSQL (Production)
