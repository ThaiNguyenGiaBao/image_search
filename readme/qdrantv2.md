# Zopi — Qdrant Vector Search Optimization

**Demo:** https://zopi-image-search.test.zopi.io/  
**Qdrant Dashboard:** http://192.168.91.30:6333/dashboard#/collections  
**Reference:** https://qdrant.tech/documentation/guides/optimize/

---

## Executive summary

This document summarizes experiments and recommended Qdrant configurations for **high-speed, low-memory**, **acceptable precision** vector search at Zopi.

**Goal:** support large-scale vector search (up to **~5M product variants**) while remaining feasible on development-class hardware — target memory budget **≤ 10 GB**.

**Key takeaways**
- End-to-end latency is dominated by **embedding (encode) time** (~600 ms on CPU), not raw vector search.
- Search latency varies dramatically with index placement: **HNSW and vectors in RAM → sub-100ms**, **on-disk → hundreds to thousands of ms**.
- For production, consider quantization + hybrid storage for the best balance.

---

## Environment

- Machine: **MacBook Pro (M4), 16 GB RAM**  
- Model inference: CPU-only (no GPU)  
- Tested datasets: **1.5M** and **5M** vectors, 768 dims

---

## Methodology

- Configurations tested: vectors/index on disk, index in RAM only, and both index+vectors in RAM.  
- Measurements: `docker stats` for resource usage; query benchmarks for latency (avg, std, median, min, max).  
- Benchmarks used representative query sets and repeated runs per configuration.

---

## Baseline

```
Machine: MacBook Pro M4, 16GB RAM (CPU-only inference)

CONTAINER ID   NAME                    CPU %     MEM USAGE / LIMIT
287eef032fc6   qdrant_1_5M_container   0.30%     117.1MiB / 7.808GiB
be157bfcd514   qdrant_5M_container     0.16%     354MiB / 7.808GiB
```

Encode benchmark (model on CPU):
```
Queries: 20
Average: 0.5770 s
Std Dev: 0.2590 s
Median : 0.5575 s
Min    : 0.2894 s
Max    : 1.4968 s
```

---

## Experiments — 1.5M vectors

### A — Vectors + HNSW index **on disk**
```
MEM USAGE: 140.7MiB
Latency (20 queries): 
  Average: 0.2233 s
  Std Dev: 0.0609 s
  Median : 0.2207 s
  Min    : 0.1485 s
  Max    : 0.3636 s
```

### B — Vectors on disk, HNSW index **in RAM**
```
MEM USAGE: 155.3MiB
Latency (50 queries):
  Average: 0.1449 s
  Std Dev: 0.0394 s
  Median : 0.1418 s
  Min    : 0.0704 s
  Max    : 0.2913 s
```

### C — Vectors + HNSW index **in RAM**
```
MEM USAGE: 4.88GiB
Latency (100 queries):
  Average: 0.0189 s
  Std Dev: 0.0135 s
  Median : 0.0136 s
  Min    : 0.0040 s
  Max    : 0.1129 s
```

**1.5M takeaway:** moving HNSW (and optionally vectors) into RAM gives large latency wins; fully in-RAM makes search negligible vs. encoding.

---

## Experiments — 5M vectors

### A — Vectors + HNSW index **on disk**
```
MEM USAGE: 372.2MiB
Latency (20 queries):
  Average: 1.6013 s
  Std Dev: 0.3166 s
  Median : 1.5370 s
  Min    : 1.1727 s
  Max    : 2.1232 s
```

### B — Vectors on disk, HNSW index **in RAM**
```
MEM USAGE: 389.9MiB
Latency (20 queries):
  Average: 1.4646 s
  Std Dev: 0.3184 s
  Median : 1.3273 s
  Min    : 1.0649 s
  Max    : 2.2958 s
```

### C — Vectors + HNSW index **in RAM**
```
MEM USAGE: 4.131GiB
Latency (20 queries):
  Average: 0.0177 s
  Std Dev: 0.0099 s
  Median : 0.0154 s
  Min    : 0.0036 s
  Max    : 0.0809 s
```

**5M takeaway:** keeping index in RAM improves latency vs full-disk, but only full in-RAM index+vectors produces millisecond-level responses. Disk I/O and index rebuild costs grow non-linearly with dataset size.

---

## Observations

- **Encode vs Search**
  - With CPU inference, **encoding (~0.58s)** dominates total request latency when search is very fast. Optimizing the encoder (caching, batching, GPU) gives the highest ROI.
- **Storage placement**
  - **All in RAM**: best latency (~0.018–0.02s measured), but requires multiple GBs of memory (~4 GiB observed for 1.5–5M).
  - **Hybrid (index in RAM, vectors on disk)**: provides a meaningful latency reduction over fully on-disk but does not reach in-RAM performance.
  - **All on disk**: lowest memory usage (~100s MiB) but highest latency (0.2–2+ s depending on scale).
- **Memory curve**
  - Memory requirements scale with both dataset size and HNSW connectivity (`m`). Expect multi-GB budgets for low-latency production at 5M+ vectors.
- **Tuning levers**
  - `m`, `ef_construct`, `ef` (query-time) control recall vs memory and latency.
  - Quantization reduces RAM and I/O but must be warmed/validated (quality vs speed trade-off).
- **Operational**
  - Building indexes on larger build hosts and transferring storage to production is often faster and safer than building in-place on constrained hosts.
  - Monitor I/O and memory during builds; use snapshots to enable safe rollback.

---

## Recommendations & Production strategy

**Target production setup (balanced):**
- Store **vectors + payloads on disk**.  
- Keep **HNSW index + quantized vectors in RAM** (`always_ram=true`), and use `rescore=false` for queries to avoid fetching full-precision vectors.  
- Expected RAM: **~4–5 GiB** for the 5M configuration tested (depends on `m` and quantization).

**Why this layout?**
- Keeps RAM reasonable while delivering ~**~17 ms** search latency measured in our trials.
- Preserves full-precision vectors on disk for occasional rescoring or reindex operations.


**Import / index-build best practice**
- Import in batches, keep `m` low during ingestion, then rebuild index with target `m`/`ef_construct`.
- Consider building on a high-memory node and moving the index files to production.

---

## Conclusion

- For Zopi’s expected scale (~5M product variants), a **hybrid approach** (vectors on disk + HNSW + quantized vectors in RAM) offers a practical balance between memory cost (~4–5 GiB) and fast search (~tens of ms).  
- Because encoding dominates total latency in CPU-only setups, **invest first in encoder optimization** (GPU inference, batching, caching). Use index placement and HNSW tuning to meet the remaining SLA trade-offs.  
- Operationally, build large indexes on beefy hosts, transfer artifacts to production, and automate monitoring of memory, I/O, and latency.

---

## References

- Qdrant Optimization Guide — https://qdrant.tech/documentation/guides/optimize/  
- Zopi demo — https://zopi-image-search.test.zopi.io/  
- Qdrant Dashboard — http://192.168.91.30:6333/dashboard#/collections

---

## Contact

For questions or reproduction scripts: **baotng@intern.firegroup.io**
