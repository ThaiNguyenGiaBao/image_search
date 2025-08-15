# Similarity Image Search

A system for similarity-based image search using OpenCLIP embeddings and Qdrant vector database. This project processes e-commerce product images from MongoDB, generates high-quality embeddings, and stores them in a vector database for fast similarity search.

## Architecture Overview
![Architecture](image-1.png)
The system consists of several key components:

- **Image Encoder**: Uses OpenCLIP with Marqo e-commerce embeddings model
- **Vector Database**: Qdrant for storing and querying 768-dimensional vectors
- **Task Queue**: Celery with Redis for distributed processing
- **Data Source**: MongoDB containing product and variant information
- **Monitoring**: Flower for Celery task monitoring

## Installation

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f celery
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Create a `.env` file with the following variables:

```bash
# MongoDB Configuration
MONGO_URI=mongodb://username:password@host:port/database

# Qdrant Configuration  
QDRANT_URI=https://your-qdrant-instance.com
QDRANT_API_KEY=your-api-key
QDRANT_TIMEOUT=120

# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Optional: Preload model on worker startup
PRELOAD_MODEL=1
```

## Usage

### Starting the System

#### Using Make Commands

```bash
# Start Celery worker
make worker

# Start Flower monitoring (available at http://localhost:5555)
make flower

# Start producer to begin processing
make producer
```

#### Manual Commands

```bash
# Start worker with model preloading
cd src && PRELOAD_MODEL=1 celery -A celery_app worker --loglevel=INFO --concurrency=4

# Start Flower monitoring
cd src && celery -A celery_app flower --port=5555

# Start producer
cd src && python producer.py
```

### Processing Workflow
![Workflow](image.png)

1. **Producer** ([src/producer.py](src/producer.py)) reads products from MongoDB in batches
2. **Celery tasks** process each product's image variants
3. **OpenCLIP Encoder** ([src/embedding/openclip_encoder.py](src/embedding/openclip_encoder.py)) generates 768-dim embeddings
4. **Qdrant Client** ([src/vectorstore/qdrant.py](src/vectorstore/qdrant.py)) stores vectors with metadata

### Scaling Workers

```bash
# Increase worker concurrency
make worker WORKER_CONCURRENCY=8

# Or with docker-compose
docker-compose up --scale celery=3
```

## Dependencies

- **Core**: Python 3.13+
- **ML**: `open_clip_torch`, `transformers`, `accelerate`
- **Database**: `pymongo`, `qdrant-client`
- **Task Queue**: `celery`, `redis`
- **Monitoring**: `flower`

## License

This project is developed by FireGroup for similarity-based image search applications.
