# Django News Application

A comprehensive news platform built with Django that allows readers to access articles from independent journalists and curated publications with role-based content management.

## Features

### User Roles & Permissions
- **Readers**: Subscribe to publishers/journalists and view approved articles
- **Journalists**: Create, edit, and manage articles and newsletters
- **Editors**: Review, approve, and manage content from journalists, oversee publishing houses

### Core Functionality
- User authentication with role-based access control
- Article creation, editing, and approval workflow
- Publishing house registration and management
- Subscription system for publishers and journalists
- RESTful API for third-party integrations
- MariaDB/MySQL database integration

## Technology Stack

- **Backend**: Django 5.2.6
- **Database**: MariaDB/MySQL
- **API**: Django REST Framework
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Authentication**: Django Auth with custom user model

## Installation

### Prerequisites
- Python 3.8+
- MariaDB/MySQL
- pip (Python package manager)
- virtualenv (recommended)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd news-project