# Videoflix Backend

This is the backend service for the **Videoflix** project, developed using Django. The backend is responsible for handling data storage, API endpoints, and business logic.

## Prerequisites

Make sure you have the following installed on your system:

- Python 3.12.0
- pip (Python package installer)
- virtualenv (to create isolated Python environments)

## Installation

Follow these steps to set up and run the project locally:

### 1. Clone the repository

Clone this repository to your local machine:

git clone https://github.com/Landvoigt/Videoflix_backend.git

### 2. Change into the project directory:

cd Videoflix_backend

### 3. Create and activate a virtual environment:

# Create virtual environment

python -m venv venv

# Activate the virtual environment
# On Windows:

venv\Scripts\activate

# On macOS/Linux:

source venv/bin/activate

### 4. Install dependencies:

pip install -r requirements.txt

### 5. Apply migrations:

python manage.py migrate

### 6. Run the development server:

python manage.py runserver
