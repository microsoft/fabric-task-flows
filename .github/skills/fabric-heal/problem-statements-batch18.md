# Problem Statements for Stress Testing

> Auto-generated batch 18 — 50 problems for self-healing loop. Focus: maximizing coverage through diverse architecture signals, testing stop-word filtering, compound tech terms.

## Architecture Patterns

1. "We need a medallion architecture with bronze, silver, and gold layers. Bronze ingests raw data, silver cleanses and deduplicates, gold serves curated business metrics."

2. "Our event sourcing architecture captures every state change as an immutable event. We need to rebuild aggregate views from the event log efficiently."

3. "We want to implement CQRS where the write path optimizes for transactional throughput and the read path optimizes for analytical query performance."

4. "The microservices architecture means each service owns its data. We need a way to create unified analytical views without tight coupling."

5. "We need a kappa architecture where everything is treated as a stream, eliminating the need for a separate batch processing layer."

## Ingestion Patterns

6. "Data arrives via REST API webhooks, SFTP file drops, database CDC streams, and manual CSV uploads. Each source has different reliability guarantees."

7. "Our ingestion layer needs to handle 500,000 events per second during peak hours and scale down to 10,000 during off-hours."

8. "Source systems push data in JSON, XML, Avro, and Protobuf formats. We need format normalization at the ingestion boundary."

9. "Late-arriving data from mobile devices with intermittent connectivity needs to be correctly placed in the historical timeline, not just appended."

10. "We need idempotent ingestion so that duplicate messages from retry logic don't create duplicate records in the downstream store."

## Transformation & Modeling

11. "Our transformation layer needs to support both SQL-based transformations for analysts and Python-based transformations for data scientists."

12. "We want incremental processing where only changed data gets reprocessed, not the entire dataset every time."

13. "Star schema modeling works for our BI use cases but the ML team needs denormalized wide tables. We need to serve both from the same source."

14. "Our slowly changing dimension implementation needs to support both Type 2 (historical tracking) and Type 1 (overwrite) depending on the attribute."

15. "Transformation dependencies form a complex DAG with over 200 nodes. We need automated dependency resolution and parallel execution."

## Serving & Consumption

16. "Analysts need sub-second query response on curated datasets. Data scientists need to run full-table scans on raw data. Both work on the same platform."

17. "Our reporting layer serves 5,000 concurrent users during the morning peak when everyone checks their dashboards."

18. "We need to expose curated metrics through both a REST API for application integration and a SQL endpoint for ad-hoc analysis."

19. "The executive dashboard must show data no older than 15 minutes. Department dashboards can tolerate hourly refreshes."

20. "External partners need read-only access to specific pre-approved datasets through a secure data sharing mechanism."

## Data Lifecycle

21. "Hot data needs sub-second access, warm data can tolerate seconds, and cold data can be archived to cheap storage with minutes-level retrieval."

22. "Regulatory requirements mandate 7-year retention for financial data, 3-year for operational data, and 90-day for debug logs."

23. "We need automated data archival that moves data through storage tiers based on access frequency and business rules."

24. "Expired data must be cryptographically erased, not just deleted, to comply with our defense contracts."

25. "Our data lifecycle policy needs to handle the contradiction between GDPR right-to-erasure and financial services record-keeping obligations."

## Cross-Cutting Concerns

26. "Every dataset needs row-level security so that regional managers only see data from their region."

27. "We need end-to-end encryption for data at rest and in transit, with key rotation every 90 days."

28. "Our disaster recovery RPO is 1 hour and RTO is 4 hours. The current backup strategy only meets RPO of 24 hours."

29. "We need to tag every dataset with its classification level, data owner, refresh frequency, and quality score."

30. "Cost allocation needs to be granular enough that we can charge each department for their actual compute and storage consumption."

## Minimal Signal Tests

31. "Lakehouse."

32. "Real-time ETL."

33. "Feature engineering pipeline."

34. "Anomaly detection."

35. "Data mesh governance."

## Non-Standard Phrasing

36. "The warehouse is too slow and nobody can find what they need in the lake."

37. "We've got spreadsheets coming out of our ears and dashboards nobody reads."

38. "The ML models are great in the notebook but fall apart when we try to productionize them."

39. "Our batch window is shrinking but our data is growing — we're going to hit a wall soon."

40. "The streaming pipeline works beautifully until it doesn't, and then we have no idea what went wrong."

## Integration Scenarios

41. "Salesforce data needs to be combined with web analytics from Google Analytics and financial data from our ERP for a complete customer view."

42. "Our IoT gateway aggregates data from Modbus, OPC-UA, and MQTT protocols and needs to normalize them into a common schema."

43. "We need to sync our Shopify order data with our warehouse management system and our accounting platform in near-real-time."

44. "Clinical trial data from EDC systems, lab information systems, and wearable devices needs to be integrated for safety monitoring."

45. "We ingest social media sentiment scores, news article topics, and market price feeds to power our trading signal generation."

## Capacity Planning

46. "Our data volume doubles every 8 months and our current infrastructure has 6 months of headroom left."

47. "Query concurrency is limited to 20 simultaneous users but we have 200 analysts who need access during business hours."

48. "The morning ETL job consumes 80% of cluster resources, starving the interactive query workload that analysts depend on."

49. "Our current storage costs are growing linearly but our query performance is degrading quadratically as data volume increases."

50. "We need to plan compute capacity for Black Friday traffic which is 10x our normal daily volume."
