# Interactive English Assessment Website

### How to start the service
 python manage.py runserver
 
## Overview
A Django-based web application that evaluates a user's English proficiency via multiple-choice quizzes. Users can register, log in, select a quiz, and receive immediate feedback after each question.

## Features
- User registration and login (with password hashing)
- Random selection of N quiz questions per attempt
- Immediate feedback (correct/incorrect with an explanation)
- Quiz attempt history stored in the database
- Responsive, clean UI via Django templates

## Technologies
- Python (Django)
- SQLite (default; easily switchable to PostgreSQL/MySQL)

## Setup Instructions
1. **Clone the Repository:**

## how to run the server:
- located in english_assessment
- run: python manage.py runserver

---

### Table Documentation  
**Table Name**: `quiz_quizattempt`  
**Description**:  
This table records each user's quiz attempt, including the timestamp of completion, the final score, and the associated user. It serves as the parent record for the `quiz_answer` table, which stores individual responses to questions. Each row represents a single completed quiz session.  

---

### Column Documentation  
| Column Name   | Data Type | Nullable? | Description |  
|---------------|-----------|-----------|-------------|  
| `id`          | INT       | NOT NULL  | **Primary Key**. Unique identifier for the quiz attempt record. Auto-incremented. |  
| `date_taken`  | DATETIME  | NOT NULL  | Timestamp of when the quiz was completed. Automatically populated on creation (via Django's `auto_now_add`). |  
| `score`       | INT       | NOT NULL  | Final score of the quiz attempt, calculated as the number of correct answers. |  
| `user_id`     | INT       | NOT NULL  | **Foreign Key** to `auth_user.id`. Identifies the user who took the quiz. |  

---

### Relationships  
- **`user_id` → `auth_user.id`**  
  Each quiz attempt is linked to a specific user in the `auth_user` table.  
- **`quiz_quizattempt.id` → `quiz_answer.quiz_attempt_id`**  
  A quiz attempt can have multiple answers stored in the `quiz_answer` table (one-to-many relationship).  

---