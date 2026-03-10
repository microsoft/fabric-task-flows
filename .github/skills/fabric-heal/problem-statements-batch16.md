# Problem Statements for Stress Testing

> Auto-generated batch 16 — 50 problems for self-healing loop. Focus: testing whether expanded stop words correctly exclude non-signal words while preserving real signal detection across varied phrasing styles.

## Data Platform Architecture Decisions

1. "We're debating whether to use a single unified lakehouse or separate specialized data stores for different workloads."

2. "Our data architecture needs to support both low-latency operational queries and complex analytical aggregations without one degrading the other."

3. "We need to decide between a centralized data team model and an embedded analytics model where each product team has their own data engineer."

4. "The question is whether we should invest in a real-time streaming layer now or wait until our batch processing foundation is solid."

5. "We need an architecture that can ingest data from both structured transactional systems and unstructured document repositories."

## Pipeline Reliability & Testing

6. "Our data pipeline has no automated tests — we only discover problems when end users report wrong numbers in their reports."

7. "We need circuit breakers in our data pipelines so that one failed upstream source doesn't corrupt everything downstream."

8. "Schema drift from source systems is our number one cause of pipeline failures. We need schema enforcement at ingestion."

9. "We want to implement data pipeline observability — tracing, metrics, and alerting — similar to what application teams have for microservices."

10. "Our testing strategy needs to cover both data correctness and performance regression as data volumes grow."

## Self-Service Analytics

11. "Analysts should be able to explore curated datasets, build their own dashboards, and share insights without involving the engineering team."

12. "We need a semantic layer that translates technical table structures into business-friendly dimensions and measures."

13. "Our self-service initiative failed because users couldn't find the right dataset and when they did, they didn't trust the numbers."

14. "We want a natural language interface where executives can ask questions about business performance and get instant visual answers."

15. "The gap between what analysts need and what the data team delivers is causing shadow IT — people are building their own data pipelines in spreadsheets."

## Streaming Analytics & CEP

16. "We need complex event processing that can detect patterns across multiple event streams — for example, when event A happens followed by event B within 5 minutes, trigger action C."

17. "Our fraud detection system processes card transactions but needs to correlate them with login events, device fingerprints, and location data in real time."

18. "We want to compute running totals, moving averages, and percentile distributions on streaming data with exactly-once processing guarantees."

19. "Clickstream events need to be sessionized in real time and enriched with user profile data before landing in the analytics store."

20. "We need to detect trending topics from social media firehose data within minutes, not hours."

## Data Privacy & Governance

21. "We need to implement column-level encryption where different user roles can see different levels of detail in the same dataset."

22. "Our data governance framework needs automated data classification — scanning all datasets to identify and tag PII, PHI, and financial data."

23. "We want to implement data lineage that traces every metric in the executive dashboard back through every transformation to the original source record."

24. "Purpose-based access control: the same dataset should be accessible to the marketing team for segmentation but not for individual-level profiling."

25. "We need automated compliance reporting that continuously monitors our data practices against GDPR, CCPA, and industry-specific regulations."

## Real-World Migration Pain

26. "We're migrating from an on-premises Informatica ETL platform to cloud-native tools. 200 jobs, most undocumented, some running since 2012."

27. "Three acquisitions in two years means we now have four different customer master databases with overlapping but inconsistent records."

28. "The vendor we chose two years ago just got acquired and their product roadmap is uncertain. We need a migration contingency plan."

29. "We built everything on a single-node PostgreSQL database and it served us well until we hit 500GB. Now everything is slow and we need to scale."

30. "Our data lake migration stalled at 60% because the remaining 40% involves complex stored procedures with business logic embedded in SQL."

## Advanced ML & AI

31. "We need an MLOps pipeline that handles model versioning, experiment tracking, automated retraining, and A/B testing in production."

32. "Our NLP pipeline needs to process customer support tickets in 12 languages, extract intent and entities, and route to the appropriate team."

33. "We want to implement RAG over our internal knowledge base so employees can ask questions and get answers grounded in company documents."

34. "The recommendation engine needs to handle cold-start problems — new users with no history and new products with no interaction data."

35. "We need to detect anomalies in our financial transactions using both supervised models trained on known fraud patterns and unsupervised models for novel attacks."

## Edge Cases & Contradictions

36. "We need real-time analytics but our budget only allows for batch processing infrastructure."

37. "The compliance team wants immutable audit logs but the privacy team wants the ability to delete any record on request."

38. "We want a serverless, zero-maintenance data platform that also gives us full control over tuning and optimization."

39. "Our data needs to be both completely open for democratization and tightly locked down for security."

40. "We want machine learning but we only have 200 rows of training data."

## Ultra-Short Stress Tests

41. "Streaming joins."

42. "Schema enforcement."

43. "Column encryption."

44. "Pipeline observability."

45. "Data lineage."

## Technical Architecture Phrases

46. "Implement exactly-once semantics for our event processing pipeline with windowed aggregations and late-arriving data handling."

47. "We need a lambda architecture with a speed layer for real-time views and a batch layer for comprehensive historical analysis."

48. "Our CQRS implementation needs an event store, projection engine, and read model synchronization with eventual consistency guarantees."

49. "Build a feature store with offline batch computation, online serving with sub-millisecond latency, and point-in-time correctness for training."

50. "Implement a data mesh with domain-oriented data products, federated computational governance, and self-serve data infrastructure."
