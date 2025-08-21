from db.mongo import Mongo


mongo = Mongo("DropshipProducts", "ae_dropship_products")
products_cursor = mongo.find(limit=20)   # or whatever iterator your Mongo wrapper returns

for product in products_cursor:
    print("== Product", product.get("source_product_id"))
    for variant in product.get("variants", []):
        options = []
        for option in variant.get("sku_property", []):
            options.append(option.get("sku_property_value", "null"))
        print(f" {', '.join(options)}")
