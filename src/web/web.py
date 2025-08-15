from fastapi import FastAPI
from main import encoder, qdrantClient
app = FastAPI()

@app.get("/")
def searchProductsByImage(image_url: str):
    """
    Search for products by image URL.
    """
    print(f"Searching for products with image: {image_url}")
    if not encoder:
        return {"error": "Encoder not initialized. Set PRELOAD_MODEL=1 to initialize."}
    
    try:
        # Encode the image URL to get the vector
        vector = encoder.encode_image(image_url)
        # Perform the search in Qdrant
        results = qdrantClient.query_points(query_vector=vector, limit=10)
        return {"data": results}
    except Exception as e:
        return {"error": str(e)}

