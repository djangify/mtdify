# MTDify

![MTD UK Bookkeeping Software](https://github.com/djangify/mtdify/blob/9752bd38249676297c8e1e88fc151dbeccf84538/mtdify-bookkeeping-dashboard.png)

<p align="center">
  <strong>Manage Transactions Daily</strong><br>
  A lightweight, self-hosted bookkeeping tool for UK sole traders and the self-employed.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#local-development">Local Development</a> •
  <a href="#self-hosted-deployment">Self-Hosted Deployment</a> •
  <a href="#documentation">Documentation</a>
</p>

---

## Overview

MTDify is a Django-based bookkeeping application designed specifically for UK sole traders and self-employed individuals. It provides a simple, privacy-focused way to track income, expenses, and VAT—all while keeping your data under your complete control.

**Key Principles:**

- **You own your data** — Everything is stored locally in SQLite
- **Privacy first** — No cloud dependencies, no data sharing
- **Simple and focused** — Built for sole traders, not enterprise accounting
- **UK tax year aware** — Automatically handles April-to-April tax years and UK dates.

## Features

- **Transaction Management** — Track income and expenses with categorisation
- **VAT Calculations** — Automatic VAT rate application and tracking
- **Quarterly Summaries** — View your finances by UK tax quarters (Q1-Q4)
- **Tax Year Reports** — Year-to-date profit/loss statements
- **CSV Exports** — Export all your data when needed
- **Receipt Storage** — Attach receipt images to expenses
- **Recurring Entries** — Set up automatic monthly transactions
- **Daily Backups** — Automatic database backups - backups appear at /app/data/db/backups/ inside the container
- **Multi-user Ready** — Support for multiple user accounts

### Admin Interface

MTDify uses [Adminita](https://github.com/djangify/adminita), a clean and modern Django admin theme. Adminita provides a new look for the Django admin panel with improved typography, spacing, and visual hierarchy.

## Quick Start

Choose your preferred deployment method:

| Method | Best For | Difficulty |
|--------|----------|------------|
| [Local Development](#local-development) | Testing, development, personal use on your machine | Easy |
| [Self-Hosted (Docker)](#docker-deployment) | Production server deployment | Medium |
| [Self-Hosted (Manual)](#manual-deployment) | VPS/dedicated server without Docker | Medium |

---

## Local Development

Run MTDify locally on your machine for development, testing, or personal use. This method runs the Django development server which is perfect for single-user scenarios.

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/djangify/mtdify.git
   cd mtdify
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your configuration (see [Configuration](#configuration) below).

5. **Initialize the database**

   ```bash
   python manage.py migrate
   ```

6. **Create a superuser account**

   ```bash
   python manage.py createsuperuser
   ```

   Or create a default demo user:

   ```bash
   python manage.py create_default_user
   ```

   This creates a user with email `demo@example.com` and password `demo123`.

7. **Collect static files**

   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Run the development server**

   ```bash
   python manage.py runserver
   ```

9. **Access the application**

   Open your browser and navigate to:
   - **Application:** http://127.0.0.1:8000
   - **Admin Panel:** http://127.0.0.1:8000/admin

### Running on a Different Port

```bash
python manage.py runserver 0.0.0.0:8080
```

### Accessing from Other Devices on Your Network

To access MTDify from other devices (phone, tablet, other computers):

1. Add your local IP to `ALLOWED_HOSTS` in `.env`:
   ```
   ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100
   ```

2. Run the server binding to all interfaces:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

3. Access from other devices at `http://192.168.1.100:8000` (use your actual local IP).

---

## Self-Hosted Deployment

Deploy MTDify on your own server for production use with multiple users or remote access.

### Docker Deployment

The recommended way to deploy MTDify in production.

#### Prerequisites

- Docker and Docker Compose installed
- A domain name (optional, for HTTPS)

#### Quick Docker Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/djangify/mtdify.git
   cd mtdify
   ```

2. **Create environment file**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with production settings:

   ```env
   DEBUG=False
   SECRET_KEY=your-very-long-random-secret-key-here
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   ```

   Generate a secure secret key:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Build and start the container**

   ```bash
   docker-compose up -d --build
   ```

4. **Run initial setup**

   ```bash
   # Run migrations
   docker-compose exec web python manage.py migrate
   
   # Create superuser
   docker-compose exec web python manage.py createsuperuser
   
   # Collect static files
   docker-compose exec web python manage.py collectstatic --noinput
   ```

5. **Access the application**

   - **HTTP:** http://your-server-ip:8000
   - **With reverse proxy:** https://your-domain.com

#### Docker Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f web

# Run Django management commands
docker-compose exec web python manage.py <command>

# Restart services
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build
```

#### Docker Data Persistence

Data is persisted in Docker volumes:

| Volume | Purpose |
|--------|---------|
| `mtdify_data` | SQLite database and media files |
| `mtdify_static` | Collected static files |

To backup your data:

```bash
# Backup database
docker-compose exec web cp /app/data/db/db.sqlite3 /app/data/db/backup-$(date +%Y%m%d).sqlite3

# Copy backup to host
docker cp mtdify_web_1:/app/data/db/backup-*.sqlite3 ./backups/
```

### Manual Deployment

Deploy without Docker on a VPS or dedicated server.

#### Prerequisites

- Python 3.11+
- A web server (Nginx recommended)
- Supervisor or systemd for process management

#### Setup Steps

1. **Clone and configure**

   ```bash
   git clone https://github.com/djangify/mtdify.git
   cd mtdify
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with production settings
   ```

3. **Initialize application**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```

4. **Create systemd service**

   Create `/etc/systemd/system/mtdify.service`:

   ```ini
   [Unit]
   Description=MTDify Gunicorn Daemon
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/mtdify
   Environment="PATH=/path/to/mtdify/.venv/bin"
   ExecStart=/path/to/mtdify/.venv/bin/gunicorn \
       --workers 3 \
       --bind unix:/path/to/mtdify/mtdify.sock \
       mtdify.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:

   ```bash
   sudo systemctl enable mtdify
   sudo systemctl start mtdify
   ```

5. **Configure Nginx**

   Create `/etc/nginx/sites-available/mtdify`:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location /static/ {
           alias /path/to/mtdify/staticfiles/;
       }

       location /media/ {
           alias /path/to/mtdify/data/media/;
       }

       location / {
           proxy_pass http://unix:/path/to/mtdify/mtdify.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Enable the site:

   ```bash
   sudo ln -s /etc/nginx/sites-available/mtdify /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

6. **Set up HTTPS (recommended)**

   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG` | Enable debug mode | `True` | No |
| `SECRET_KEY` | Django secret key | `change-me-in-production` | **Yes (production)** |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` | **Yes (production)** |

#### Example `.env` for Development

```env
DEBUG=True
SECRET_KEY=dev-secret-key-not-for-production
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### Example `.env` for Production

```env
DEBUG=False
SECRET_KEY=your-super-long-random-secret-key-minimum-50-characters
ALLOWED_HOSTS=mtdify.yourdomain.com,www.mtdify.yourdomain.com
```

### Security Considerations

When `DEBUG=False`, the following security features are automatically enabled:

- HTTPS redirect (`SECURE_SSL_REDIRECT`)
- Secure session cookies (`SESSION_COOKIE_SECURE`)
- Secure CSRF cookies (`CSRF_COOKIE_SECURE`)
- CSRF trusted origins based on `ALLOWED_HOSTS`

**Important:** Always use HTTPS in production and ensure your reverse proxy sets the `X-Forwarded-Proto` header.

---

## Project Structure

```
mtdify/
├── accounts/           # User authentication and management
├── bookkeeping/        # Core transaction tracking
│   ├── models.py       # Income, Expense, Category, RecurringEntry
│   ├── views/          # Transaction and report views
│   └── utils.py        # Tax year utilities
├── business/           # Business profile management
├── mtdify/             # Django project settings
│   ├── settings.py     # Application configuration
│   ├── urls.py         # URL routing
│   └── views.py        # Dashboard and home views
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── data/               # SQLite database and media (gitignored)
│   ├── db/             # Database files
│   └── media/          # Uploaded receipts
├── requirements.txt    # Python dependencies
├── manage.py           # Django management script
├── Dockerfile          # Docker image definition
└── docker-compose.yml  # Docker Compose configuration
```

---

## Usage Guide

### First-Time Setup

1. **Log in** with your created account
2. **Create a Business** — Navigate to Business → Add Business
3. **Set your tax year** — The system defaults to the current UK tax year
4. **Start tracking** — Add income and expenses from the dashboard

### Personalising Reports

When you generate printable reports, MTDify displays your email address by default. To include your full name and business name on reports:

1. Go to **Admin Panel** (`/admin`)
2. Navigate to **Users** and select your account
3. Add your **First Name** and **Last Name**
4. Ensure you've created a **Business** with your business name

Reports will then display your name, email, and business name in the header — useful for professional record-keeping.

### Adding Transactions

**Income:**
- Navigate to Bookkeeping → Add Income
- Enter date, description, amount, and category
- Optionally add client name and invoice number

**Expenses:**
- Navigate to Bookkeeping → Add Expense
- Enter date, description, amount, and category
- Set VAT rate (0%, 5%, or 20%)
- Upload receipt image (optional)

### Reports

Access reports from the Dashboard:

- **Quarterly Summary** — View income, expenses, and profit by quarter
- **Category Breakdown** — See spending by category
- **CSV Export** — Download data for your accountant

### Tax Years

MTDify follows the UK tax year (6 April – 5 April):

- **Q1:** April – June
- **Q2:** July – September  
- **Q3:** October – December
- **Q4:** January – March

Switch between tax years using the dropdown in the navigation bar.

---

## API Reference

MTDify does not currently expose a public API. All interactions are through the web interface.

---

## Troubleshooting

### Common Issues

**"CSRF verification failed"**
- Ensure `ALLOWED_HOSTS` includes your domain
- Check that your reverse proxy passes the `X-Forwarded-Proto` header

**Static files not loading**
- Run `python manage.py collectstatic --noinput`
- Check that WhiteNoise is properly configured (it is by default)

**Database locked errors**
- SQLite can have issues with concurrent writes
- For heavy multi-user scenarios, consider PostgreSQL

**Permission denied on data directory**
- Ensure the application user has write access to `data/` directory
- In Docker, check volume permissions

### Getting Help

- **Documentation:** 
- **Issues:** https://github.com/djangify/mtdify/issues

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Clone your fork
3. Create a virtual environment and install dependencies
4. Create a branch for your feature
5. Make your changes
6. Run tests (when available)
7. Submit a pull request

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgements

Built with:

- [Django](https://www.djangoproject.com/) — The web framework
- [django-allauth](https://django-allauth.readthedocs.io/) — Authentication
- [WhiteNoise](http://whitenoise.evans.io/) — Static file serving
- [Gunicorn](https://gunicorn.org/) — WSGI server
- [Tailwind CSS](https://tailwindcss.com/) — Styling

---

<p align="center">
  Made with ❤️ for UK sole traders<br>
  <a href="https://todiane.com/blog/introducing-mtdify/">Introducing Manage Transactions Daily</a>
</p>
