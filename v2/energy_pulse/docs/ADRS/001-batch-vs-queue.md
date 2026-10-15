# ADR — File microbatch before event queue

**Decision:** use deterministic JSONL files and independently invoked producer/ingest/build commands for the first reference implementation. The raw file hash and event ID make replay auditable; SQLite transactions, quarantine and run IDs make failure visible. This is **not streaming**.

**Reason:** the demo's first job is proving correct source-to-result movement, idempotence, late policy and lineage. Kafka/Redpanda/Redis Streams would add orchestration and failure surfaces before a delivery-SLA requirement exists. A queue becomes justified only after a measured need for sustained parallel ingestion, delivery guarantees, consumer lag monitoring and recovery is documented and tested. The current single-writer SQLite design is explicitly bounded.
