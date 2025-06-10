#!/bin/bash

# Setup script for bare metal Nginx with Docker containers
# This script helps set up Nginx on bare metal to work with Docker containers

echo "Setting up Nginx for bare metal with Docker containers..."

# 1. Create directories for media files
echo "Creating media directories..."
sudo mkdir -p /var/www/palpal/media
sudo mkdir -p /var/www/palpal/static

# 2. Set proper permissions
echo "Setting permissions..."
sudo chown -R www-data:www-data /var/www/palpal
sudo chmod -R 755 /var/www/palpal

# 3. Copy nginx configuration
echo "Setting up Nginx configuration..."
sudo cp nginx-bare-metal.conf /etc/nginx/sites-available/palpal

# 4. Enable the site
echo "Enabling site..."
sudo ln -sf /etc/nginx/sites-available/palpal /etc/nginx/sites-enabled/

# 5. Remove default site if exists
sudo rm -f /etc/nginx/sites-enabled/default

# 6. Test nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid!"
    echo "You can now:"
    echo "1. Start your Docker containers: docker compose -f docker-compose.production.yml up -d"
    echo "2. Restart Nginx: sudo systemctl restart nginx"
    echo "3. Check status: sudo systemctl status nginx"
    echo ""
    echo "Your application will be available at:"
    echo "- Main app: http://159.223.48.89"
    echo "- Flower monitoring: http://159.223.48.89:5555"
    echo ""
    echo "Note: Make sure to mount the Docker media volume to /var/www/palpal/media"
    echo "You can do this by adding a bind mount to your docker-compose.yml:"
    echo "volumes:"
    echo "  - production_django_media:/app/palpal/media"
    echo "  - /var/www/palpal/media:/app/palpal/media"
else
    echo "Nginx configuration has errors. Please check the configuration."
    exit 1
fi
