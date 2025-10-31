# Load Balancing Guide

This guide explains how to configure load balancing for the Face Authentication and De-duplication System.

## Overview

The system is designed to be stateless and can be horizontally scaled across multiple instances. Load balancing distributes incoming traffic across these instances to:

- Improve availability and fault tolerance
- Increase throughput and handle more concurrent requests
- Enable zero-downtime deployments
- Provide geographic distribution

## Health Check Endpoints

The system provides three health check endpoints for load balancer integration:

### 1. `/health` - Basic Health Check

**Purpose**: Quick health check for load balancers

**Response Codes**:

- `200`: Service is healthy
- `503`: Service is unhealthy

**Checks**:

- Database connectivity

**Usage**: Use this for basic load balancer health checks

```bash
curl http://localhost:8000/health
```

**Response**:

```json
{
  "status": "healthy",
  "service": "face-auth-system",
  "version": "1.0.0",
  "timestamp": "2024-10-31T12:00:00.000000"
}
```

### 2. `/live` - Liveness Probe

**Purpose**: Kubernetes liveness probe

**Response Codes**:

- `200`: Application is running

**Checks**:

- Application is responsive (no dependency checks)

**Usage**: Use this for Kubernetes liveness probes to detect if the application needs restart

```bash
curl http://localhost:8000/live
```

### 3. `/ready` - Readiness Probe

**Purpose**: Comprehensive readiness check

**Response Codes**:

- `200`: Service is ready to accept traffic
- `503`: Service is not ready

**Checks**:

- Database connectivity
- Service dependencies
- System resources

**Usage**: Use this for Kubernetes readiness probes and detailed health monitoring

```bash
curl http://localhost:8000/ready
```

## Load Balancing Strategies

### 1. Round Robin

Distributes requests evenly across all backend servers.

**Pros**:

- Simple and fair distribution
- Works well with similar server capacities

**Cons**:

- Doesn't account for server load
- May send requests to busy servers

**Use Case**: Homogeneous server environment with similar workloads

### 2. Least Connections

Routes requests to the server with the fewest active connections.

**Pros**:

- Better load distribution
- Adapts to varying request durations

**Cons**:

- Slightly more complex
- Requires connection tracking

**Use Case**: Recommended for this system (default in our configs)

### 3. IP Hash

Routes requests from the same client IP to the same server.

**Pros**:

- Session affinity without cookies
- Predictable routing

**Cons**:

- Uneven distribution with few clients
- Not needed for stateless APIs

**Use Case**: Not recommended for this system (stateless design)

## Nginx Configuration

### Installation

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

### Configuration

Copy the provided configuration:

```bash
sudo cp config/nginx-load-balancer.conf /etc/nginx/sites-available/face-auth
sudo ln -s /etc/nginx/sites-available/face-auth /etc/nginx/sites-enabled/
```

### Update Backend Servers

Edit `/etc/nginx/sites-available/face-auth`:

```nginx
upstream face_auth_backend {
    least_conn;

    # Replace with your actual server IPs
    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8000 max_fails=3 fail_timeout=30s;
}
```

### SSL Certificates

Generate or obtain SSL certificates:

```bash
# Self-signed (development only)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/key.pem \
  -out /etc/nginx/ssl/cert.pem

# Let's Encrypt (production)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d api.faceauth.example.com
```

### Test and Reload

```bash
# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx
```

### Monitoring

```bash
# View access logs
sudo tail -f /var/log/nginx/face_auth_access.log

# View error logs
sudo tail -f /var/log/nginx/face_auth_error.log

# Check nginx status
curl http://localhost:8080/nginx-status
```

## HAProxy Configuration

### Installation

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install haproxy

# CentOS/RHEL
sudo yum install haproxy
```

### Configuration

Copy the provided configuration:

```bash
sudo cp config/haproxy-load-balancer.cfg /etc/haproxy/haproxy.cfg
```

### Update Backend Servers

Edit `/etc/haproxy/haproxy.cfg`:

```haproxy
backend face_auth_backend
    server worker1 10.0.1.10:8000 check inter 5s fall 3 rise 2
    server worker2 10.0.1.11:8000 check inter 5s fall 3 rise 2
    server worker3 10.0.1.12:8000 check inter 5s fall 3 rise 2
```

### SSL Certificate

Combine certificate and key:

```bash
cat /path/to/cert.pem /path/to/key.pem > /etc/haproxy/certs/face_auth.pem
chmod 600 /etc/haproxy/certs/face_auth.pem
```

### Test and Restart

```bash
# Test configuration
sudo haproxy -c -f /etc/haproxy/haproxy.cfg

# Restart HAProxy
sudo systemctl restart haproxy

# Check status
sudo systemctl status haproxy
```

### Monitoring

```bash
# View logs
sudo tail -f /var/log/haproxy.log

# Access statistics page
# Open browser: http://your-server:8404/stats
```

## Kubernetes Configuration

### Service and Ingress

```yaml
apiVersion: v1
kind: Service
metadata:
  name: face-auth-service
spec:
  selector:
    app: face-auth-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: face-auth-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.faceauth.example.com
      secretName: face-auth-tls
  rules:
    - host: api.faceauth.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: face-auth-service
                port:
                  number: 80
```

### Health Checks

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: face-auth-api
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: api
          image: face-auth-api:latest
          ports:
            - containerPort: 8000
          livenessProbe:
            httpGet:
              path: /live
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
```

## AWS Application Load Balancer

### Target Group Configuration

```bash
# Create target group
aws elbv2 create-target-group \
  --name face-auth-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# Register targets
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=i-xxxxx Id=i-yyyyy Id=i-zzzzz
```

### Load Balancer Configuration

```bash
# Create load balancer
aws elbv2 create-load-balancer \
  --name face-auth-lb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

## Testing Load Balancer

### Basic Connectivity

```bash
# Test health endpoint
curl https://api.faceauth.example.com/health

# Test with multiple requests
for i in {1..10}; do
  curl -s https://api.faceauth.example.com/health | jq .
  sleep 1
done
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 https://api.faceauth.example.com/health

# Using wrk
wrk -t4 -c100 -d30s https://api.faceauth.example.com/health

# Using hey
hey -n 1000 -c 10 https://api.faceauth.example.com/health
```

### Verify Load Distribution

Check backend server logs to ensure requests are distributed:

```bash
# On each backend server
tail -f /var/log/face-auth/access.log | grep "Request completed"
```

## Troubleshooting

### Backend Server Not Receiving Traffic

1. Check health check status:

```bash
# Nginx
curl http://backend-ip:8000/health

# HAProxy stats page
# Check server status in stats UI
```

2. Verify firewall rules:

```bash
# Check if port 8000 is accessible
telnet backend-ip 8000
```

3. Check backend logs:

```bash
tail -f /var/log/face-auth/app.log
```

### High Response Times

1. Check backend server resources:

```bash
# CPU and memory
top
htop

# Network
netstat -an | grep 8000
```

2. Adjust load balancer timeouts:

```nginx
# Nginx
proxy_connect_timeout 60s;
proxy_send_timeout 120s;
proxy_read_timeout 120s;
```

3. Scale horizontally (add more backend servers)

### SSL/TLS Issues

1. Verify certificate:

```bash
openssl s_client -connect api.faceauth.example.com:443
```

2. Check certificate expiration:

```bash
echo | openssl s_client -connect api.faceauth.example.com:443 2>/dev/null | openssl x509 -noout -dates
```

## Best Practices

1. **Use HTTPS**: Always use SSL/TLS in production
2. **Health Checks**: Configure appropriate health check intervals
3. **Timeouts**: Set reasonable timeouts for long-running requests
4. **Rate Limiting**: Implement rate limiting at load balancer level
5. **Monitoring**: Monitor backend server health and response times
6. **Logging**: Enable access and error logging
7. **Security Headers**: Add security headers at load balancer
8. **Connection Pooling**: Use keep-alive connections
9. **Graceful Shutdown**: Handle SIGTERM for zero-downtime deployments
10. **Auto-scaling**: Configure auto-scaling based on metrics

## Monitoring and Alerts

### Key Metrics to Monitor

- Backend server health status
- Request rate and response times
- Error rates (4xx, 5xx)
- Connection counts
- SSL certificate expiration
- Load balancer CPU and memory

### Example Prometheus Queries

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Response time (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Backend health
up{job="face-auth-backend"}
```

## Conclusion

Proper load balancing is essential for high-availability and scalable deployments. Choose the load balancer that best fits your infrastructure and follow the best practices outlined in this guide.
