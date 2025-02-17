# Run the service
python manage.py runserver

# Interactive Quiz Website

## Overview
A Django-based web application that evaluates a user's English proficiency via multiple-choice quizzes. Users can register, log in, select a quiz, and receive immediate feedback after each question.

## Features
- User registration and login (with password hashing)
- Random selection of 5 quiz questions per attempt
- Immediate feedback (correct/incorrect with an explanation)
- Quiz attempt history stored in the database
- Responsive, clean UI via Django templates

## Technologies
- Python (Django)
- SQLite (default; easily switchable to PostgreSQL/MySQL)

## Setup Instructions
1. **Clone the Repository:**
