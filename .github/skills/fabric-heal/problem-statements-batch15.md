# Problem Statements for Stress Testing

> Auto-generated batch 15 — 50 problems for self-healing loop. Focus: data products, democratization at scale, real-time ML inference, time-series analytics, data fabric, DataOps, unusual phrasing and metaphors.

## DataOps & Pipeline Engineering

1. "We need CI/CD for our data pipelines — version control, automated testing, and deployment pipelines just like our application developers have."

2. "Schema validation happens only in production. By the time we catch a problem, bad data has already propagated to three downstream systems."

3. "Our pipeline orchestrator has 800 DAGs and nobody can tell which ones are still actively used versus orphaned from decommissioned projects."

4. "We want canary deployments for data transformations — run the new logic on a subset of data and compare outputs before switching over."

5. "Every environment has slightly different data, making it impossible to reproduce production issues in staging."

## Time-Series Analytics

6. "We collect temperature, humidity, and pressure readings every 5 seconds from 2,000 sensor locations and need to detect anomalies within one minute."

7. "Our financial trading system needs to compute rolling 30-day VWAP across millions of ticker symbols with updates every second."

8. "Energy consumption data comes in 15-minute intervals and we need to forecast demand 48 hours ahead to optimize grid capacity."

9. "Server performance metrics need to be retained at full resolution for 30 days, then downsampled to hourly for a year, then daily for five years."

10. "We need to correlate equipment vibration patterns with failure events that happened weeks or months later to build predictive models."

## Data Democratization at Scale

11. "We have 500 analysts across 20 departments and every one of them wants a different view of the same underlying data."

12. "The data team gets 200 ad-hoc requests per week and can only deliver on 30. The other 170 requestors wait or make something up."

13. "Business users need to combine their departmental data with enterprise datasets without needing to understand the data model."

14. "We built a data marketplace but adoption is only 12% after six months because people can't find what they need."

15. "Power users want SQL access, casual users want drag-and-drop dashboards, and executives want automated email summaries. One platform needs to serve all three."

## Real-Time ML Inference

16. "Credit scoring decisions need to be made in under 100 milliseconds using the latest transaction history and a model that's retrained daily."

17. "Our content moderation system needs to classify user-generated content in real time before it's visible to other users."

18. "We want to deploy an LLM-powered chatbot that retrieves context from our enterprise knowledge base and responds in under 2 seconds."

19. "The dynamic pricing engine needs to consider current inventory, competitor prices scraped in real-time, and demand signals from web traffic."

20. "Autonomous quality inspection on the production line uses computer vision models that must process camera frames at 30 FPS."

## Data Fabric & Integration

21. "We need to query data across our data warehouse, NoSQL database, and object storage without moving it into a single system."

22. "Our data integration layer handles 50 different source systems with different protocols, formats, and refresh schedules."

23. "We want metadata-driven automation where the system discovers new data sources and automatically applies the right ingestion and transformation patterns."

24. "Our API gateway handles 10,000 requests per second and each request needs to join real-time context with historical customer profile data."

25. "The data fabric should handle schema mapping, data quality rules, and access policies automatically based on metadata tags."

## Metaphorical & Storytelling Style

26. "Our data landscape is like a city that grew without urban planning — there are highways to nowhere, buildings connected by footpaths, and no one has a map."

27. "We're trying to drink from a fire hose of data while our plumbing was designed for a garden hose."

28. "Think of our current situation as a library where every book is shelved randomly, there's no card catalog, and the librarian quit."

29. "Our data pipeline is like a Rube Goldberg machine — it works, but nobody wants to touch it because the whole thing might collapse."

30. "We need to go from a situation where data is treated like exhaust to one where it's treated like fuel."

## Performance & Optimization

31. "Dashboard load times exceed 30 seconds and users have given up and gone back to spreadsheets."

32. "Our nightly ETL window is shrinking as the business operates across more time zones. We're running out of downtime for processing."

33. "Join performance degrades exponentially as we add more fact tables to our star schema queries."

34. "The same aggregation is being computed by 15 different queries across the organization. We need materialized views or pre-computation."

35. "Full table scans on our 2TB fact table take 45 minutes. We need partitioning or indexing strategies that don't require a complete rebuild."

## Regulatory & Compliance Edge Cases

36. "We operate in financial services and need to demonstrate that no human can modify audit trail records once they're written."

37. "Our data retention policy requires automated deletion, but our legal hold process requires preserving everything related to active litigation."

38. "Cross-border data transfers between the EU and US require standard contractual clauses, and we need to prove our data platform enforces them."

39. "The regulator requires that we can produce a complete history of all changes to any customer record within 24 hours of a request."

40. "We need to implement purpose limitation — data collected for billing can only be used for billing, not for marketing analytics."

## Adversarial & Trick Questions

41. "We don't actually have a data problem, we have a people problem. But management told us to buy a data platform anyway."

42. "Our data is perfect, our pipelines never fail, and everyone agrees on the metrics. We just need to make it faster."

43. "We need a blockchain-based data lake with quantum-resistant encryption and AI-generated schemas."

44. "Can you build us a data platform that requires zero maintenance, has infinite scalability, and costs nothing?"

45. "We want to predict the future with 100% accuracy using our historical data."

## Concise Technical

46. "Snowflake to Fabric migration, 200TB, 90-day timeline."

47. "Event sourcing with CQRS pattern, 50K events per second, eventual consistency acceptable."

48. "Multi-tenant data isolation with shared compute, row-level security, per-tenant encryption keys."

49. "Streaming ETL from Kafka to lakehouse, exactly-once semantics, schema registry integration."

50. "Feature engineering pipeline: 500 features, hourly refresh, point-in-time correctness required."
