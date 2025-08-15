from src.vectorstore.qdrant import Qdrant
from src.db.mongo import Mongo
import numpy as np
import hashlib
from qdrant_client.models import PointStruct, ScoredPoint

qdrantClient = Qdrant(
    url="",
    api_key = "",
    collection_name="test_products"
)


mongo = Mongo("",
                "DropshipProducts",
                "amazon_products")



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

id = 1
points = []
TOTAL_BATCH = 1000
current_batch = 0
for i in range(TOTAL_BATCH):
    current_batch += 1
    print(f"Processing batch {current_batch}...")
    products = mongo.find(limit=600, skip=i*600)
    for product in products:
        # generate embeddings for the main product image
        p_vec = embed_product(product["source_product_id"])
        for variant in product['variants']:
            payload = {
                "source_product_id": product['source_product_id'],
                "source_variant_id": variant['sku_id'],
                "image": variant['image'],
                "source": "amazon",
                "options": product['options'],
            }
            
            # generate embedding for variant by adding noise to product image vector
            v_vec = embed_variant(p_vec, variant["sku_id"], noise_scale=0.15)
            points.append(
                PointStruct(
                    id=id,
                    vector=to_list(v_vec),
                    payload=payload
                )
            )
            id += 1
            
            if id % 200 == 0:
                print(f"Upserting {id} points...")
                qdrantClient.upsert_points(points)
                points = []
        
   
        
    
