from embedding.openclip_encoder import OpenClipEncoder
from fastapi import FastAPI
from main import qdrantClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import time


encoder = OpenClipEncoder()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to ["http://127.0.0.1:5500"] etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/encode_image")
def encode_image(image_url: str):

    print(f"Searching for products with image: {image_url}")
    if not encoder:
        return {"error": "Encoder not initialized. Set PRELOAD_MODEL=1 to initialize."}
    
    try:
        # Encode the image URL to get the vector
        vector = encoder.encode_image(image_url)
     
        return {"data": vector}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/search")
def search_image(image_url: str):
    """
    Search for products by image URL.
    """
    print(f"Searching for products with image: {image_url}")
    if not encoder:
        return {"error": "Encoder not initialized. Set PRELOAD_MODEL=1 to initialize."}
    
    start_total = time.perf_counter()
    
    try:
        
        # Encode the image URL to get the vector
        start_encode = time.perf_counter()
        vector = encoder.encode_image(image_url)
        encode_time = time.perf_counter() - start_encode
        
        # Perform the search in Qdrant
        start_query = time.perf_counter()
        results = qdrantClient.query_points(query_vector=vector, limit=20)
        query_time = time.perf_counter() - start_query

        return_data = []
        for point in results.points: 
            return_data.append({
                "id": point.id,
                "score": point.score,
                "source_product_id": point.payload.get("source_product_id"),
                "source_variant_id": point.payload.get("source_variant_id"),
                "image": point.payload.get("image"),
                "source": point.payload.get("source"),
                "options": point.payload.get("options"),
            })
            
        total_time = time.perf_counter() - start_total
        return {"data": return_data, 
               "timing": {
                    "encode_time_sec": encode_time,
                    "query_time_sec": query_time,
                    "total_time_sec": total_time
                    }
               }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def root():
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(file_path)
