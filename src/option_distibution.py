from collections import defaultdict
from typing import Iterable, Dict, Any

# --- Helper function ---
def group_variant_properties(products: Iterable[Dict[str, Any]], normalize_names: bool = True):
    """
    For each product, group variant.sku_property by sku_property_name -> list of distinct values.
    Returns (enriched_products, global_map)
      - enriched_products: list of products with 'grouped_properties' added (dict)
      - global_map: dict of property_name -> sorted list of distinct values across all products
    """
    global_map = defaultdict(set)
    enriched = []

    for product in products:
        grouped = defaultdict(list)   # preserve insertion order for values
        seen_for_name = defaultdict(set)  # to ensure distinct values per property (fast lookup)

        variants = product.get("variants") or []
        for variant in variants:
            for prop in variant.get("sku_property") or []:
                name = prop.get("sku_property_name")
                value = prop.get("sku_property_value")

                if name is None:
                    continue

                key = name.strip().lower() if normalize_names else name.strip()

                # treat None or empty string values gracefully
                if value is None:
                    v = ""
                else:
                    v = str(value).strip().lower() 

                # only append unique values (preserve the order of first appearance)
                if v not in seen_for_name[key]:
                    grouped[key].append(v)
                    seen_for_name[key].add(v)

                # update global aggregation
                global_map[key].add(v)

        # attach grouped properties back to product (or collect separately)
        # convert defaultdict(list) -> regular dict for nicer printing/JSON
        product["grouped_properties"] = dict(grouped)
        enriched.append(product)

    # convert global_map sets -> sorted lists
    global_map_out = {k: sorted(list(v)) for k, v in global_map.items()}
    return enriched, global_map_out

# --- Usage example with your Mongo client ---
from db.mongo import Mongo

mongo = Mongo("DropshipProducts", "ae_dropship_products")
products_cursor = mongo.find(limit=1000)   # or whatever iterator your Mongo wrapper returns

enriched_products, global_props = group_variant_properties(products_cursor, normalize_names=True)

# Print per-product grouped properties (example)
for p in enriched_products:
    pid = p.get("source_product_id") or p.get("_id")
    print("Product:", pid)
    for prop_name, values in p["grouped_properties"].items():
        print("  -", prop_name, ":", values)
    print()

# Print global aggregation of property -> values
print("Global aggregated properties:")
for k, vals in global_props.items():
    print(" -", k, "->", vals)
