# MoneyMap Installation Guide

## Prerequisites
- Python 3.8 or higher
- Docker and Docker Compose
- Git
- PostgreSQL (if not using Docker)

## Installation Steps

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/MoneyMap-Project/MoneyMap.git

# Navigate to project directory
cd MoneyMap
```

### 2. Virtual Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On MacOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt
```

### 4. Environment Configuration

#### 4.1 Generate Secret Key
```bash
# Start Python interactive shell
python

# In Python shell, run:
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())

# Exit Python shell
exit()
```

#### 4.2 Setup Environment File
```bash
# On MacOS/Linux:
cp sample.env .env

# On Windows (Command Prompt):
copy sample.env .env

# Edit .env file and replace SECRET_KEY with the generated key
```

### 5. Docker Setup
- Install Docker in case you don't have it yet
```bash
# Start Docker containers
docker-compose up -d

# Verify containers are running
docker ps
```

### 6. Database Setup
```bash
# Run migrations
python manage.py migrate

# Load demo data
python manage.py loaddata data/moneymap_demo_data.json
```

### 7. Run Development Server
```bash
# Standard run
python manage.py runserver

# If CSS is not loading, use insecure mode
python manage.py runserver --insecure
```

## Troubleshooting

### CSS Not Loading
If you encounter CSS loading issues:
1. First try running with --insecure flag:
```bash
python manage.py runserver --insecure
```
2. If issues persist, check:
   - `DEBUG` setting in your .env file
   - Static files configuration in settings.py
   - Browser console for specific errors

### Docker Issues
If Docker containers fail to start:
1. Check Docker logs:
```bash
docker-compose logs
```
2. Ensure all required ports are available
3. Try rebuilding containers:
```bash
docker-compose down
docker-compose up --build -d
```

### Database Issues
If you encounter database problems:
```bash
# Reset database
python manage.py flush


# Reload demo data
python manage.py loaddata moneymap_demo_data.json
```
