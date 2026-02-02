# Celery Setup for Async Schedule Generation

## Overview

The schedule generation process can take 5+ minutes, which causes timeout issues with synchronous API requests. We've implemented Celery with Redis to handle this as an async background task.

## Architecture

```
Frontend → FastAPI → Celery → Redis → Celery Worker → Schedule Generation
   ↓                                          ↓
   Poll for status ←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

## Prerequisites

### 1. Install Redis

**Windows:**

```bash
# Option 1: Using Chocolatey
choco install redis-64

# Option 2: Using Windows Subsystem for Linux (WSL)
wsl --install
# Then in WSL:
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start

# Option 3: Download from GitHub
# https://github.com/microsoftarchive/redis/releases
# Download Redis-x64-3.2.100.msi and install
```

**Mac:**

```bash
brew install redis
brew services start redis
```

**Linux:**

```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### 2. Verify Redis is Running

```bash
redis-cli ping
# Should return: PONG
```

### 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements-api.txt
```

## Running the Application

You need to run **3 separate processes**:

### Terminal 1: Redis Server (if not running as service)

```bash
redis-server
```

### Terminal 2: FastAPI Server

```bash
cd backend
python scripts/run_api.py
```

### Terminal 3: Celery Worker

```bash
cd backend
python scripts/run_celery_worker.py
```

### Terminal 4: Frontend (optional)

```bash
cd frontend
npm run dev
```

## Environment Variables

Add to `backend/.env`:

```bash
# Redis connection (optional, defaults to localhost)
REDIS_URL=redis://localhost:6379/0
```

## API Endpoints

### 1. Start Async Schedule Generation

```http
POST /api/schedule/async
Content-Type: application/json

{
  "force_regenerate": true
}
```

**Response:**

```json
{
  "task_id": "abc123-def456-...",
  "status": "PENDING",
  "message": "Schedule generation started"
}
```

### 2. Check Task Status

```http
GET /api/schedule/status/{task_id}
```

**Response (In Progress):**

```json
{
  "task_id": "abc123-def456-...",
  "status": "PROGRESS",
  "message": "Generating schedule for 200 teams..."
}
```

**Response (Complete):**

```json
{
  "task_id": "abc123-def456-...",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "total_games": 629,
    "games": [...],
    "validation": {...},
    "generation_time": 287.5
  }
}
```

## Frontend Integration

The frontend now:

1. Calls `/api/schedule/async` to start the task
2. Receives a `task_id`
3. Polls `/api/schedule/status/{task_id}` every 2 seconds
4. Shows progress updates to the user
5. Displays the final schedule when complete

## Troubleshooting

### Redis Connection Error

```
Error: Redis connection refused
```

**Solution:**

- Make sure Redis is running: `redis-cli ping`
- Check Redis URL in `.env` file
- On Windows, make sure Redis service is started

### Celery Worker Not Processing Tasks

```
Task stays in PENDING state forever
```

**Solution:**

- Make sure Celery worker is running
- Check worker logs for errors
- Verify Redis connection in worker

### Task Timeout

```
Task takes too long and times out
```

**Solution:**

- Increase `task_time_limit` in `celery_app.py`
- Current limit: 600 seconds (10 minutes)

## Monitoring

### Check Redis Queue

```bash
redis-cli
> KEYS *
> LLEN celery  # Check queue length
```

### Check Celery Tasks

```bash
# In Python
from app.core.celery_app import celery_app
from celery.result import AsyncResult

task = AsyncResult('task-id', app=celery_app)
print(task.state)
print(task.info)
```

## Production Deployment

For production, consider:

1. **Redis Persistence**: Configure Redis to persist data
2. **Celery Supervisor**: Use supervisord or systemd to manage Celery workers
3. **Multiple Workers**: Run multiple Celery workers for parallel processing
4. **Result Backend**: Use PostgreSQL instead of Redis for result storage
5. **Monitoring**: Use Flower for Celery monitoring

### Example Supervisor Config

```ini
[program:celery_worker]
command=/path/to/venv/bin/python /path/to/backend/scripts/run_celery_worker.py
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log
```

## Testing

Test the async endpoint:

```bash
# Start task
curl -X POST http://localhost:8000/api/schedule/async \
  -H "Content-Type: application/json" \
  -d '{"force_regenerate": true}'

# Check status (replace TASK_ID with actual task ID)
curl http://localhost:8000/api/schedule/status/TASK_ID
```
