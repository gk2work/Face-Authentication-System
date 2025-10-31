# HTTPS Configuration Guide

This document provides instructions for configuring HTTPS/TLS for the Face Authentication and De-duplication System in production environments.

## Overview

HTTPS is essential for protecting sensitive data in transit, including:

- User credentials during authentication
- JWT tokens
- Applicant personal information
- Facial photographs
- API requests and responses

## Production Deployment with HTTPS

### Option 1: Using Uvicorn with SSL Certificates

For direct HTTPS support in Uvicorn:

1. **Obtain SSL Certificates**

   You can obtain SSL certificates from:
   - Let's Encrypt (free, automated)
   - Commercial Certificate Authorities
   - Self-signed certificates (for testing only)

2. **Using Let's Encrypt with Certbot**

   ```bash
   # Install certbot
   sudo apt-get update
   sudo apt-get install certbot

   # Obtain certificate
   sudo certbot certonly --standalone -d yourdomain.com

   # Certificates will be saved to:
   # /etc/letsencrypt/live/yourdomain.com/fullchain.pem
   # /etc/letsencrypt/live/yourdomain.com/privkey.pem
   ```

3. **Run Uvicorn with SSL**

   ```bash
   uvicorn app.main:app \
     --host 0.0.0.0 \
     --port 443 \
     --ssl-keyfile /etc/letsencrypt/live/yourdomain.com/privkey.pem \
     --ssl-certfile /etc/letsencrypt/live/yourdomain.com/fullchain.pem \
     --workers 4
   ```

4. **Update backend/run.py for Production**

   ```python
   import uvicorn
   from app.core.config import settings

   if __name__ == "__main__":
       if settings.ENVIRONMENT == "production":
           uvicorn.run(
               "app.main:app",
               host=settings.API_HOST,
               port=443,
               ssl_keyfile="/etc/letsencrypt/live/yourdomain.com/privkey.pem",
               ssl_certfile="/etc/letsencrypt/live/yourdomain.com/fullchain.pem",
               workers=settings.API_WORKERS,
               log_level="info"
           )
       else:
           uvicorn.run(
               "app.main:app",
               host=settings.API_HOST,
               port=settings.API_PORT,
               reload=True,
               log_level="debug"
           )
   ```

### Option 2: Using Nginx as Reverse Proxy (Recommended)

Using Nginx as a reverse proxy provides additional benefits:

- SSL termination
- Load balancing
- Static file serving
- Rate limiting
- DDoS protection

1. **Install Nginx**

   ```bash
   sudo apt-get update
   sudo apt-get install nginx
   ```

2. **Obtain SSL Certificate**

   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Configure Nginx**

   Create `/etc/nginx/sites-available/face-auth-system`:

   ```nginx
   # Redirect HTTP to HTTPS
   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }

   # HTTPS Server
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;

       # SSL Configuration
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

       # SSL Security Settings
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       ssl_prefer_server_ciphers on;
       ssl_session_cache shared:SSL:10m;
       ssl_session_timeout 10m;

       # Security Headers
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
       add_header X-Frame-Options "SAMEORIGIN" always;
       add_header X-Content-Type-Options "nosniff" always;
       add_header X-XSS-Protection "1; mode=block" always;

       # Client body size limit (for photograph uploads)
       client_max_body_size 10M;

       # Proxy settings
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;

           # Timeouts
           proxy_connect_timeout 60s;
           proxy_send_timeout 60s;
           proxy_read_timeout 60s;
       }

       # Health check endpoint (no auth required)
       location /health {
           proxy_pass http://127.0.0.1:8000/health;
           access_log off;
       }
   }
   ```

4. **Enable Configuration**

   ```bash
   sudo ln -s /etc/nginx/sites-available/face-auth-system /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Run Application**

   ```bash
   # Application runs on localhost:8000 (HTTP)
   # Nginx handles HTTPS and forwards to application
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
   ```

### Option 3: Using Docker with Traefik

For containerized deployments with automatic SSL:

1. **docker-compose.yml with Traefik**

   ```yaml
   version: "3.8"

   services:
     traefik:
       image: traefik:v2.10
       command:
         - "--api.insecure=false"
         - "--providers.docker=true"
         - "--entrypoints.web.address=:80"
         - "--entrypoints.websecure.address=:443"
         - "--certificatesresolvers.letsencrypt.acme.email=admin@yourdomain.com"
         - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
         - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - "/var/run/docker.sock:/var/run/docker.sock:ro"
         - "./letsencrypt:/letsencrypt"

     app:
       build: .
       labels:
         - "traefik.enable=true"
         - "traefik.http.routers.app.rule=Host(`yourdomain.com`)"
         - "traefik.http.routers.app.entrypoints=websecure"
         - "traefik.http.routers.app.tls.certresolver=letsencrypt"
         - "traefik.http.services.app.loadbalancer.server.port=8000"
       environment:
         - ENVIRONMENT=production
   ```

## Environment Variables for Production

Update `backend/.env` file for production:

```bash
# Environment
ENVIRONMENT=production

# MongoDB (use connection string with SSL)
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/face_auth_db?retryWrites=true&w=majority&ssl=true

# Security (MUST be changed from defaults)
SECRET_KEY=<generate-strong-random-key-minimum-32-characters>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_HOST=127.0.0.1  # Bind to localhost when using reverse proxy
API_PORT=8000
API_WORKERS=4

# Redis (use TLS if available)
REDIS_URL=rediss://redis:6379  # Note: rediss:// for TLS
REDIS_PASSWORD=<strong-password>
```

## Generating Strong SECRET_KEY

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

## Certificate Renewal

Let's Encrypt certificates expire after 90 days. Set up automatic renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab for automatic renewal
sudo crontab -e

# Add this line (runs twice daily)
0 0,12 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

## Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] TLS 1.2 or higher enforced
- [ ] Strong SECRET_KEY configured (minimum 32 characters)
- [ ] Default credentials changed
- [ ] CORS configured with specific allowed origins
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] File permissions set correctly (600 for files, 700 for directories)
- [ ] MongoDB connection uses SSL/TLS
- [ ] Redis connection uses TLS (if applicable)
- [ ] Environment variables protected
- [ ] Automatic certificate renewal configured

## Testing HTTPS Configuration

```bash
# Test SSL configuration
curl -I https://yourdomain.com/health

# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Test with SSL Labs
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

## Troubleshooting

### Certificate Issues

```bash
# Check certificate expiration
sudo certbot certificates

# Force certificate renewal
sudo certbot renew --force-renewal
```

### Nginx Issues

```bash
# Check Nginx configuration
sudo nginx -t

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Application Issues

```bash
# Check if application is running
curl http://localhost:8000/health

# View application logs (from project root)
tail -f backend/logs/app.log
```

## Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
