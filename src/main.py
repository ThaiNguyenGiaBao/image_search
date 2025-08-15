from vectorstore.qdrant import Qdrant
from qdrant_client.models import PointStruct    
from embedding.openclip_encoder import OpenClipEncoder
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import os 



qdrantClient = Qdrant(
    collection_name="productsV3",
    dim=768,
) 
qdrantClient.ensure_collection() 


# Lazy loading - only initialize when needed
encoder = None
if os.getenv("PRELOAD_MODEL", "0") == "1":
    encoder = OpenClipEncoder()


variant_count = 1
TOTAL_BATCH = 1000
BATCH_SIZE = 1  
current_batch = 0

def process_variant(variant, product):
    payload = {
        "source_product_id": product['source_product_id'],
        "source_variant_id": variant['sku_id'],
        "image": variant['image'],
        "source": product['source'],
        "options": product['options'],
    }
            
    v_vec = encoder.encode_image(variant["image"])
    return PointStruct(
        id=str(uuid.uuid4()),
        vector=v_vec,
        payload=payload
    )

def process_product(product):
        points = []
        seen_variants = set()
        valid_variants = [v for v in product['variants'] 
                         if v.get('image') and v['image'] not in seen_variants and not seen_variants.add(v['image'])]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_variant, variant, product) for variant in valid_variants]
            for fut in as_completed(futures):
                try:
                    points.append(fut.result())
                except Exception as e:
                    print(f"Error processing variant: {e}")
        
        if points:
            print(f"Upserting {len(points)}/ {len(product['variants'])} points...")
            qdrantClient.upsert_points(points)
                
