# Problem Statements for Stress Testing

> Auto-generated batch 19 — 50 problems for self-healing loop. Focus: high-density tech terminology, compound keywords, unusual sentence structures.

## Dense Technical Scenarios

1. "Implement a streaming ETL pipeline that reads from Kafka topics, applies schema validation via a schema registry, performs windowed aggregations, and writes to a Delta Lake table with ACID guarantees."

2. "Our data warehouse needs partitioning by date, clustering by customer ID, and materialized views that refresh incrementally every 15 minutes."

3. "Build an ML feature pipeline that computes rolling 7-day and 30-day aggregates, joins with a customer profile dimension, and serves features with sub-millisecond latency for online inference."

4. "We need a real-time fraud detection system that processes payment events, joins with historical transaction patterns, applies ML scoring, and routes suspicious transactions for human review."

5. "The data lake needs zone-based organization: landing zone for raw ingestion, conformance zone for schema enforcement, curated zone for business-ready datasets."

## Compound Architecture Requirements

6. "Our analytics platform must support batch reporting on historical data, real-time dashboards for operational monitoring, and ML model training on the combined dataset."

7. "We need a single platform that handles structured transactional data from our ERP, semi-structured logs from our web servers, and unstructured documents from our CRM."

8. "The solution must comply with SOX for financial reporting, HIPAA for patient data, and GDPR for European customer records — all in the same platform."

9. "We want a lakehouse that provides both the flexibility of a data lake for data science exploration and the performance of a data warehouse for BI queries."

10. "Our architecture needs to support both OLTP workloads for our customer-facing application and OLAP workloads for our analytics team without performance interference."

## Data Engineering Challenges

11. "Our orchestration system runs 500 DAG jobs nightly. Dependencies are implicit and undocumented, making changes risky."

12. "We need change data capture from 20 source databases with different change tracking mechanisms — some have CDC enabled, others only have timestamp columns."

13. "Data pipeline testing is non-existent. We need unit tests for transformation logic, integration tests for end-to-end correctness, and regression tests for performance."

14. "Our data lake has 2 million files in a single folder. Query performance is terrible because of small file proliferation."

15. "We need to implement data compaction, partition pruning, and Z-ordering to optimize our lakehouse query performance."

## Governance & Compliance Density

16. "Implement row-level security, column-level masking, data classification tagging, automated PII detection, and purpose-based access control across all datasets."

17. "Our data lineage must trace from the executive KPI dashboard widget through every transformation, join, and filter back to the source system table and column."

18. "We need automated data quality scoring that checks completeness, accuracy, consistency, timeliness, and uniqueness for every dataset."

19. "The compliance dashboard should show real-time violations of data access policies, retention policy breaches, and unauthorized cross-border data transfers."

20. "Implement differential privacy for aggregate analytics, synthetic data generation for development environments, and k-anonymity for published research datasets."

## ML/AI Engineering

21. "Our model registry needs to track model versions, training datasets, hyperparameters, evaluation metrics, and deployment history."

22. "We need automated model retraining triggered by data drift detection, with canary rollout and automatic rollback if performance degrades."

23. "The RAG pipeline needs vector indexing of our knowledge base, semantic search for query matching, context window management, and response grounding verification."

24. "Feature engineering automation: automatically generate candidate features from raw data, evaluate their predictive power, and register the best ones in the feature store."

25. "Our recommendation engine needs collaborative filtering, content-based filtering, and a hybrid approach that switches based on available interaction data."

## Minimal Signals

26. "Batch ETL."

27. "Streaming analytics."

28. "Data lakehouse."

29. "Predictive maintenance."

30. "Data mesh."

## Infrastructure & Operations

31. "Our Kubernetes cluster runs Spark jobs, Airflow DAGs, and Jupyter notebooks. Resource contention during peak hours causes job failures."

32. "We need auto-scaling compute that spins up within 2 minutes for burst workloads and scales to zero when idle to minimize costs."

33. "Storage tiering: hot tier for frequently accessed datasets on SSD, warm tier on standard storage, cold tier on archive storage with lifecycle automation."

34. "Our monitoring stack needs to alert on data freshness SLA violations, query performance degradation, and cost budget overruns."

35. "We need disaster recovery for our entire data platform — compute, storage, metadata, and security configurations — with cross-region failover."

## Unusual Phrasings

36. "The numbers lie because the data behind them is garbage."

37. "By the time anyone sees the report, the data is already ancient history."

38. "Every department has built their own little data empire and they refuse to share."

39. "We're sitting on a goldmine of data but we don't have the tools to extract any value from it."

40. "The pipeline is held together with prayers and cron jobs."

## Integration & Interop

41. "REST API ingestion from 50 vendor APIs, each with different rate limits, authentication mechanisms, pagination styles, and error handling requirements."

42. "We need bidirectional sync between our cloud data platform and on-premises SAP system with conflict resolution for concurrent updates."

43. "Our microservices emit domain events in CloudEvents format. We need to capture, transform, and land them in our analytical data store."

44. "Cross-cloud data federation: query data in Azure Synapse, AWS Redshift, and GCP BigQuery from a single SQL interface."

45. "We need to reconcile data between our billing system and payment processor with automated discrepancy detection and alerting."

## Capacity & Growth

46. "Our data volume is growing 300% year-over-year and our current architecture was designed for 10% growth."

47. "The real-time pipeline handles 100K events per second today but we expect 1M per second within 18 months."

48. "Our query warehouse has 500 concurrent users today but the product roadmap will expose analytics to 50,000 end-users."

49. "Storage costs are $200K per month and growing. Most of that is data that hasn't been accessed in over a year."

50. "We need an architecture that performs well at both our current 10TB scale and our projected 500TB scale without requiring a rebuild."
