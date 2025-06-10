# Bare Metal Nginx Setup for PalPal

This document explains how to set up Nginx on bare metal (host system) to work with Docker containers.

## Overview

The setup has been changed from:
- **Before**: Nginx running inside Docker container
- **After**: Nginx running on bare metal (host system), Docker containers exposing ports

## Architecture

```
Internet → Bare Metal Nginx (Port 80, 5555) → Docker Containers
                                            ├─ Django (127.0.0.1:8000)
                                            └─ Flower (127.0.0.1:5555)
```

## Prerequisites

1. Install Nginx on your system:
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. Make sure Docker and Docker Compose are installed

## Setup Instructions

### Option 1: Automatic Setup (Recommended)

Run the setup script:
```bash
./setup-nginx-bare-metal.sh
```

### Option 2: Manual Setup

1. **Create directories for media files:**
   ```bash
   sudo mkdir -p /var/www/palpal/media
   sudo mkdir -p /var/www/palpal/static
   sudo chown -R www-data:www-data /var/www/palpal
   sudo chmod -R 755 /var/www/palpal
   ```

2. **Copy Nginx configuration:**
   ```bash
   sudo cp nginx-bare-metal.conf /etc/nginx/sites-available/palpal
   ```

3. **Enable the site:**
   ```bash
   sudo ln -sf /etc/nginx/sites-available/palpal /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site
   ```

4. **Test configuration:**
   ```bash
   sudo nginx -t
   ```

## Starting the Application

1. **Start Docker containers:**
   ```bash
   docker compose -f docker-compose.production.yml up -d
   ```

2. **Start/Restart Nginx:**
   ```bash
   sudo systemctl restart nginx
   sudo systemctl enable nginx  # Enable auto-start on boot
   ```

3. **Check status:**
   ```bash
   sudo systemctl status nginx
   docker compose -f docker-compose.production.yml ps
   ```

## Accessing the Application

- **Main Application**: http://159.223.48.89
- **Flower Monitoring**: http://159.223.48.89:5555

## File Serving

- **Media files**: Served directly by Nginx from `/var/www/palpal/media/`
- **Static files**: Served directly by Nginx from `/var/www/palpal/static/`
- **Dynamic content**: Proxied to Django container

## Port Configuration

| Service | Host Port | Container Port | Bind Address |
|---------|-----------|----------------|--------------|
| Django  | 8000      | 5000          | 127.0.0.1    |
| Flower  | 5555      | 5555          | 127.0.0.1    |
| Nginx   | 80, 5555  | -             | 0.0.0.0      |

## Troubleshooting

### Check if ports are bound correctly:
```bash
netstat -tlnp | grep -E ':(80|5555|8000)'
```

### Check Nginx logs:
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check Docker container logs:
```bash
docker compose -f docker-compose.production.yml logs django
docker compose -f docker-compose.production.yml logs flower
```

### Test connectivity:
```bash
curl http://127.0.0.1:8000  # Should reach Django
curl http://127.0.0.1:5555  # Should reach Flower
```

## Media Files

The Django container will write media files to both:
1. Docker volume: `production_django_media`
2. Host directory: `/var/www/palpal/media/` (bind mount)

This allows Nginx to serve files directly from the host filesystem for better performance.

## Security Notes

- Django and Flower are only accessible from localhost (127.0.0.1)
- External access is only through Nginx
- Media and static files are served with appropriate caching headers
- Security headers are added by Nginx

## Reverting to Docker Nginx

If you need to revert to Docker-based Nginx, you can:
1. Remove the bare metal Nginx configuration
2. Restore the `compose/production/nginx/` directory
3. Update `docker-compose.production.yml` to include the nginx service
4. Remove port exposures from django and flower services
