from vectorstore.qdrant import Qdrant
from db.mongo import Mongo
import numpy as np
import hashlib
from qdrant_client.models import PointStruct, ScoredPoint
import time
import os 
import statistics
import random



qdrantClient = Qdrant(
    collection_name=os.getenv("QDRANT_COLLECTION", "Benchmark"),
    dim=768,
) 
qdrantClient.ensure_collection() 
mongo = Mongo( "DropshipProducts", "amazon_products")


DIM = 768

def _seed_from(*parts: str) -> int:
    s = "|".join(parts)
    h = hashlib.sha256(s.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "little")

def _unit(vec: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(vec)
    return vec if n == 0 else vec / n

def embed_product(key: str, dim: int = DIM) -> np.ndarray:
    """
    key: something stable like product_id or main image URL
    returns a unit-length vector (for cosine)
    """
    rng = np.random.default_rng(_seed_from("product", key))
    v = rng.normal(size=dim)
    return _unit(v)

def embed_variant(product_vec: np.ndarray, variant_key: str,
                  noise_scale: float = 0.1) -> np.ndarray:
    """
    Make a variant near the product by adding orthogonal Gaussian noise.
    noise_scale≈0.1 => cosine ≈ 0.995; 0.5 => ≈ 0.894; 1.0 => ≈ 0.707.
    """
    dim = product_vec.shape[0]
    p = _unit(product_vec)
    rng = np.random.default_rng(_seed_from("variant", variant_key))

    # random noise and remove the component along p (keep it orthogonal-ish)
    n = rng.normal(size=dim)
    n = n - (n @ p) * p
    n = _unit(n)

    v = _unit(p + noise_scale * n)
    return v

# # --- helpers (optional) ---

def noise_for_target_cosine(target_cos: float) -> float:
    """
    If variant = unit(p + s*n) with n ⟂ p, then cos = 1 / sqrt(1 + s^2).
    Solve s from target cosine.
    """
    if not (0 < target_cos <= 1):
        raise ValueError("target_cos must be in (0, 1].")
    return (1 / (target_cos**2) - 1) ** 0.5

def to_list(vec: np.ndarray) -> list[float]:
    return vec.astype(np.float32).tolist()


def benchmark(num=100):
    skip = random.randint(0, 2000)  
    print(f"Benchmarking {num} queries, starting from skip={skip}...")
    products = mongo.find(limit=1000, skip=skip)
    results = []

    for i in range(num):
        idx = random.randint(0, len(products)-1)
        product = products[idx]
        p_vec = embed_product(product["source_product_id"])

        start_time = time.time()
        qdrantClient.query_points(
            query_vector=to_list(p_vec),
            limit=20
        )
        elapsed_time = time.time() - start_time
        results.append(elapsed_time)
        print(f"Query time for product {idx}: {elapsed_time:.4f} seconds")

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

benchmark(100)


        
   
        
    
