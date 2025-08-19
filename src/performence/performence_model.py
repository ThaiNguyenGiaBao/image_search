from vectorstore.qdrant import Qdrant
from db.mongo import Mongo
import numpy as np
import hashlib
from qdrant_client.models import PointStruct, ScoredPoint
import time
import os 
import statistics
import random
from embedding.openclip_encoder import OpenClipEncoder


encode = OpenClipEncoder()

mongo = Mongo( "DropshipProducts", "amazon_products")


DIM = 768


def benchmark(num=100):
    skip = random.randint(0, 1000)  
    print(f"Benchmarking {num} queries, starting from skip={skip}...")
    products = mongo.find(limit=num, skip=skip)
    results = []

    for product in products:
        if len(product['images']) == 0:
            continue       
        start_time = time.time()
        encode.encode_image(product['images'][0])

        elapsed_time = time.time() - start_time
        results.append(elapsed_time)
        print(f"Query time for product {product['source_product_id']}: {elapsed_time:.4f} seconds")

    # stats
    avg_time = sum(results) / len(results)
    std_dev = statistics.stdev(results) if len(results) > 1 else 0.0
    min_time = min(results)
    max_time = max(results)
    median_time = statistics.median(results)

    print("\n--- Benchmark Results ---")
    print(f"Queries: {num}")
    print(f"Average: {avg_time:.4f} s")
    print(f"Std Dev: {std_dev:.4f} s")
    print(f"Median : {median_time:.4f} s")
    print(f"Min    : {min_time:.4f} s")
    print(f"Max    : {max_time:.4f} s")

    return {
        "average": avg_time,
        "std_dev": std_dev,
        "median": median_time,
        "min": min_time,
        "max": max_time,
    }

benchmark(50)


        
   
        
    
