# 🚀 Deployment Guide

This guide covers different deployment options for the Sports Meet Event Management System.

## 🌐 Streamlit Cloud (Recommended)

### Prerequisites

* GitHub account
* Supabase project set up
* Code pushed to a public GitHub repository

### Step-by-Step Deployment

1. **Prepare Your Repository**
   ```bash
   git add .
   git commit -m "Initial commit - Sports Meet Manager"
   git push origin main
   ```
2. **Deploy to Streamlit Cloud**
   * Visit [share.streamlit.io](https://share.streamlit.io/)
   * Click "New app"
   * Connect your GitHub repository
   * Select the repository and branch
   * Set main file path: `main.py`
   * Click "Deploy"
3. **Configure Secrets**
   In your Streamlit Cloud app settings, add these secrets:
   ```toml
   [secrets]
   SUPABASE_URL = "your_supabase_project_url"
   SUPABASE_KEY = "your_supabase_anon_key"
   ```
4. **Verify Deployment**
   * Your app will be available at: `https://your-app-name.streamlit.app`
   * Test all functionality to ensure proper connection

### Automatic Updates

* Any push to your main branch will automatically redeploy the app
* Monitor the deployment logs in Streamlit Cloud dashboard

## 🐳 Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the application
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build and Run

```bash
# Build the image
docker build -t sports-meet-manager .

# Run with environment variables
docker run -p 8501:8501 \
  -e SUPABASE_URL="your_supabase_url" \
  -e SUPABASE_KEY="your_supabase_key" \
  sports-meet-manager
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    env_file:
      - .env
    restart: unless-stopped

volumes:
  app_data:
```

Run with:

```bash
docker-compose up -d
```

## ☁️ Heroku Deployment

### Prerequisites

* Heroku CLI installed
* Heroku account

### Setup Files

1. **Create `Procfile`**
   ```
   web: streamlit run main.py --server.port=$PORT --server.address=0.0.0.0
   ```
2. **Create `setup.sh`**
   ```bash
   mkdir -p ~/.streamlit/

   echo "\
   [server]\n\
   headless = true\n\
   enableCORS = false\n\
   port = $PORT\n\
   " > ~/.streamlit/config.toml
   ```
3. **Update `Procfile`**
   ```
   web: sh setup.sh && streamlit run main.py
   ```

### Deploy to Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-sports-meet-app

# Set environment variables
heroku config:set SUPABASE_URL="your_supabase_url"
heroku config:set SUPABASE_KEY="your_supabase_key"

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

## 🖥️ VPS/Server Deployment

### Using Nginx + Gunicorn

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   pip3 install -r requirements.txt
   ```
2. **Create Systemd Service**
   Create `/etc/systemd/system/sports-meet.service`:
   ```ini
   [Unit]
   Description=Sports Meet Manager
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/var/www/sports-meet
   Environment=SUPABASE_URL=your_url
   Environment=SUPABASE_KEY=your_key
   ExecStart=/usr/local/bin/streamlit run main.py --server.port 8501
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. **Configure Nginx**
   Create `/etc/nginx/sites-available/sports-meet`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```
4. **Enable and Start Services**
   ```bash
   # Enable Nginx site
   sudo ln -s /etc/nginx/sites-available/sports-meet /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx

   # Start application service
   sudo systemctl enable sports-meet
   sudo systemctl start sports-meet
   ```

## 📱 Mobile-Optimized Deployment

### PWA Configuration

Add to your Streamlit config:

```python
st.set_page_config(
    page_title="Sports Meet Manager",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="collapsed",  # Better for mobile
    menu_items={
        'Get Help': 'https://github.com/your-repo/issues',
        'Report a bug': "https://github.com/your-repo/issues",
        'About': "Sports Meet Event Management System"
    }
)
```

### Mobile-Specific CSS

```css
@media (max-width: 768px) {
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
  
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem;
    }
}
```

## 🔒 Security Considerations

### Environment Variables

Never commit sensitive data. Use:

* `.env` files for local development
* Cloud platform secrets for production
* Environment variables for containers

### Database Security

1. **Enable Row Level Security (RLS)** in Supabase:
   ```sql
   ALTER TABLE students ENABLE ROW LEVEL SECURITY;
   ALTER TABLE events ENABLE ROW LEVEL SECURITY;
   ALTER TABLE results ENABLE ROW LEVEL SECURITY;
   ```
2. **Create Policies** (example):
   ```sql
   -- Allow read access to all authenticated users
   CREATE POLICY "Allow read access" ON students FOR SELECT TO authenticated USING (true);

   -- Allow insert for authenticated users
   CREATE POLICY "Allow insert access" ON students FOR INSERT TO authenticated WITH CHECK (true);
   ```

### HTTPS Configuration

Always use HTTPS in production:

* Streamlit Cloud automatically provides HTTPS
* For custom deployments, use Let's Encrypt or Cloudflare

## 📊 Monitoring & Maintenance

### Health Checks

Add health check endpoint:

```python
# Add to main.py
def health_check():
    try:
        db = DatabaseManager()
        db.get_all_students()  # Test DB connection
        return {"status": "healthy", "timestamp": datetime.now()}
    except:
        return {"status": "unhealthy", "timestamp": datetime.now()}
```

### Logging

Configure logging for production:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Backup Strategy

1. **Database Backups** : Use Supabase automated backups
2. **Code Backups** : Git repository
3. **Data Exports** : Regular CSV exports of results

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   * Verify Supabase URL and key
   * Check network connectivity
   * Ensure tables exist
2. **Import Errors**
   * Verify all dependencies in `requirements.txt`
   * Check Python version compatibility
   * Rebuild virtual environment
3. **Memory Issues**
   * Optimize database queries
   * Implement pagination for large datasets
   * Consider caching strategies

### Performance Optimization

1. **Database Indexing**
   ```sql
   CREATE INDEX IF NOT EXISTS idx_results_event_position ON results(event_id, position);
   CREATE INDEX IF NOT EXISTS idx_students_house_bib ON students(house, bib_id);
   ```
2. **Streamlit Caching**
   ```python
   @st.cache_data(ttl=300)  # Cache for 5 minutes
   def get_cached_results():
       return db.get_all_results()
   ```
3. **Connection Pooling**
   Consider implementing connection pooling for high-traffic deployments.

---

## 📞 Support

If you encounter issues during deployment:

1. Check the application logs
2. Verify environment variables
3. Test database connectivity
4. Review Supabase dashboard for errors
5. Create an issue on GitHub with deployment details
