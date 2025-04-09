# Django React Sheet Application

A web application built with Django (backend) and React (frontend) providing a spreadsheet-like interface with versioning, permissions, and ToDo features.

## Setup and Run (Docker)

Prerequisites:
*   Docker
*   Docker Compose

1.  **Clone Repository:**
    ```bash
    # git clone <your-repo-url> # Or extract the provided code
    cd django-react-sheetapp
    ```
2.  **Create `.env` file:** Copy `.env.example` to `.env` and fill in the required values. **Crucially, generate a strong, unique `DJANGO_SECRET_KEY`**.
    ```bash
    cp .env.example .env
    # Use a text editor like nano or vim to edit .env
    # nano .env
    ```
3.  **Build Docker Images:**
    ```bash
    docker-compose build
    ```
4.  **Start Services:**
    ```bash
    docker-compose up -d
    ```
    *(Wait ~30 seconds for services to initialize and DB to become healthy)*
5.  **Apply Database Migrations:**
    ```bash
    docker-compose exec backend python manage.py migrate
    ```
6.  **Create Superuser (Admin):**
    ```bash
    docker-compose exec backend python manage.py createsuperuser
    ```
    *(Follow prompts to set email and password)*

7.  **Access:**
    *   **Frontend:** http://localhost:3000
    *   **Django Admin:** http://localhost:8000/admin/ (Login with the superuser credentials you just created)

8.  **Stopping:**
    ```bash
    docker-compose down
    ```

## Tech Stack

*   **Backend:** Django, Django Rest Framework
*   **Frontend:** React, Tailwind CSS, Axios, React Router
*   **Database:** PostgreSQL
*   **Containerization:** Docker, Docker Compose

## Features

*   User Authentication (Register/Login/Logout) with CSRF Protection
*   Page Creation & Management
*   Spreadsheet-like Interface (Rows, Columns, Cells)
*   Editable Cells and Structure (Add/Remove Rows/Columns)
*   Column Resizing (Basic Width Persistence)
*   ToDo List Generation from Pages
*   Status Tracking for ToDo Items
*   Snapshot-based Versioning
*   Permission System (Public/Private, View/Edit/Manage per User/Group - Basic implementation)
*   Dark/Light Theme Toggle
*   Party Mode! 😎