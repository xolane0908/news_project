# News Project - Django Application

## Setup with Virtual Environment
1. \python -m venv venv\
2. \env\\Scripts\\Activate\
3. \pip install -r requirements.txt\
4. \python manage.py migrate\
5. \python manage.py runserver\

## Setup with Docker
1. \docker build -t news-project .\
2. \docker run -p 8000:8000 news-project\

Access: http://localhost:8000
