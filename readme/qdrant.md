
[Link demo](https://zopi-image-search.test.zopi.io/)
[Dataset](http://192.168.91.30:6333/dashboard#/collections)
Dataset when evaluating: 1.5M variants

# Config qdrant to optimize for Zopi need

[Link](https://qdrant.tech/documentation/guides/optimize/)
- Different use cases require different balances between memory usage, search speed, and precision. In the case of Zopi, we need:
    - High Precision & Low Memory Usage

The reason is the bottleneck in similarity search is not the query time (~100ms), but the encode time (~600ms) for about 1.5M variants.
=> we store both vectors and the HNSW index on disk + increase the layer of HNSW index



To store the vectors on_disk, you need to configure both the vectors and the HNSW index:

```
PUT /collections/{collection_name}
{
    "vectors": {
      "size": 768,
      "distance": "Cosine",
      "on_disk": true
    },
    "hnsw_config": {
        "on_disk": true
    }
}
```

Increase the ef and m parameters of the HNSW index to improve precision, even with limited RAM:
```
"hnsw_config": {
    "m": 64,
    "ef_construct": 512,
    "on_disk": true
}
```
