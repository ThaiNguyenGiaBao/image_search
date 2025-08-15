from db.mongo import Mongo
from celery_app import task_process_batch_products  
import random
import os

#mongo = Mongo( "DropshipProducts", "amazon_products")
mongo = Mongo( "DropshipProducts", "ae_dropship_products")

BATCH_SIZE = 1000
current_batch =  int(os.getenv("START_BATCH", "0"))
    

amazon_projection = {
    "_id": 0,
    "variants.sku_id": 1,
    "variants.image": 1, 
    "source_product_id": 1, 
    "options": 1, 
    "source": 1,
}

aliexpress_projection = {
    "_id": 0,
    "variants": 1,
    "images": 1,
    "source_product_id": 1,
    "options": 1,
    "source": 1
}



def normalize_aliexpress_products(products):
    nomalized_products = []    
    for product in products:
        try: 
            nomalized_product = {
                "source_product_id": product["source_product_id"],
                "variants": [],
                "options": [],
                "source": "aliexpress"
            }
            for option in product.get("options", []):
                nomalized_product["options"].append(option['name'])
                    
            for variant in product.get("variants", []):
                variant = {
                    "sku_id": variant.get("aliexpress_sku_id", ""),
                    "image": variant.get('sku_property')[0].get('sku_image', "") if variant.get('sku_property') else ""
                }
                if not variant["image"]:
                    variant["image"] = product.get("images", [])[random.randint(0, len(product.get("images", [])) - 1)] 
                    
                nomalized_product["variants"].append(variant)
            nomalized_products.append(nomalized_product)
        except Exception as e:
            print(f"Error normalizing product {product.get('source_product_id', 'unknown')}: {e}")
    return nomalized_products


    
while True:
    print(f"Processing batch {current_batch}...")
    products = mongo.find(limit=BATCH_SIZE, skip=current_batch*BATCH_SIZE, projection=aliexpress_projection)

    if not products:    
        print("No more products to process.")
        break
    
    task_process_batch_products.delay(normalize_aliexpress_products(products))
    
    current_batch += 1
  
                
                        