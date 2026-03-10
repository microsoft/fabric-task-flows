# Problem Statements for Stress Testing

> Auto-generated batch 20 — 50 problems for self-healing loop. Focus: edge cases, single-keyword triggers, maximal tech density, and natural conversation patterns.

## Single Keyword Triggers

1. "We need streaming."

2. "Our batch processing is broken."

3. "Machine learning pipeline."

4. "Data quality framework."

5. "Compliance automation."

6. "Real-time dashboard."

7. "Data warehouse migration."

8. "API integration layer."

9. "Predictive analytics."

10. "Data governance."

## Maximum Tech Density

11. "Build a streaming ingestion pipeline with schema registry validation, exactly-once semantics, windowed aggregation, and real-time anomaly detection feeding both a lakehouse gold layer and a low-latency serving endpoint."

12. "Our medallion architecture needs automated data quality gates between bronze and silver layers, incremental processing with merge operations, and materialized views in the gold layer with row-level security."

13. "Implement an ML feature platform with offline batch feature computation via Spark, online feature serving with Redis, point-in-time correctness for training dataset generation, and feature drift monitoring."

14. "We need a sensitive data platform with column-level encryption, automated PII classification, data lineage tracking, purpose-based access control, GDPR deletion workflows, and cross-border transfer monitoring."

15. "Deploy a lambda architecture with a Kafka-based speed layer for sub-second event processing, a Spark-based batch layer for comprehensive historical reprocessing, and a serving layer that merges both views."

## Natural Conversation

16. "Look, we've been dumping everything into a data lake for two years and it's become completely unusable. Can we actually organize this thing?"

17. "My boss saw a demo of real-time analytics and now wants everything to be real-time, even the monthly financial report. How do we manage expectations?"

18. "We're a startup that just got Series B funding. We need to build our data infrastructure from scratch. Where do we start?"

19. "The data science team keeps asking for clean data and the data engineering team keeps saying the data IS clean. Who's right?"

20. "We had a data breach last quarter and now security is everyone's top priority. What architectural changes should we make?"

## Progressive Complexity

21. "We have CSV files."

22. "We have CSV files that need to be loaded into a database."

23. "We have CSV files from multiple sources that need to be cleaned, deduplicated, and loaded into a database daily."

24. "We have CSV files from multiple sources with different schemas that need to be cleaned, deduplicated, loaded into a database daily, and served through dashboards that refresh every morning."

25. "We have CSV files from multiple sources with different schemas that need to be cleaned, deduplicated, loaded into a database daily, served through dashboards that refresh every morning, with ML models that predict trends and compliance reports that track data lineage."

## Architecture Decision Points

26. "Should we use a lakehouse or keep our data warehouse and data lake separate?"

27. "Is event-driven architecture the right choice when most of our workloads are batch-oriented with a few real-time exceptions?"

28. "We're choosing between a centralized data platform and a data mesh. What factors should drive this decision?"

29. "Our team is debating between building on top of managed services versus deploying open-source tools we control."

30. "Should we invest in data quality tooling or data governance tooling first?"

## Error Recovery & Resilience

31. "When our ingestion pipeline fails mid-batch, we need to resume from where it left off without reprocessing everything."

32. "Our streaming pipeline occasionally processes events out of order. We need to handle this gracefully without corrupting downstream aggregations."

33. "Schema changes from upstream sources should be detected, quarantined, and handled without bringing down the entire pipeline."

34. "We need automated backfill capabilities when we discover that historical data was processed incorrectly."

35. "Our data reconciliation process runs weekly but takes 3 days. By the time discrepancies are found, the source data has already changed."

## Data Product Thinking

36. "Each domain team should publish their data as a product with an SLA, schema documentation, quality metrics, and a feedback mechanism."

37. "We want a data marketplace where teams can discover, preview, and request access to datasets with automated approval workflows."

38. "Our data products need versioning so that consumers can pin to a specific version and migrate to newer versions at their own pace."

39. "Usage analytics for our data products: who queries what, how often, which joins are most common, and which datasets are never accessed."

40. "Data product health scoring based on freshness, completeness, consistency, documentation coverage, and consumer satisfaction."

## Performance Optimization

41. "Our most popular dashboard takes 45 seconds to load. It joins 8 tables with 2 billion total rows."

42. "Nightly ETL runtime has grown from 2 hours to 8 hours over the past year. We need to optimize or parallelize."

43. "Ad-hoc queries from data scientists routinely scan terabytes of data and impact BI query performance for business users."

44. "Our incremental processing pipeline reprocesses too much data because the change detection logic is overly broad."

45. "We need to implement query result caching with intelligent invalidation when underlying data changes."

## Extreme Edge Cases

46. "Everything."

47. "Nothing."

48. "Data."

49. "Help us build a data platform that uses every type of Fabric item available."

50. "Our problem isn't data — it's that we have too much of it, can't find any of it, don't trust what we find, and can't process it fast enough when we do."
