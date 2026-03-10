# Problem Statements for Stress Testing

> Auto-generated batch 17 — 50 problems for self-healing loop. Focus: operational analytics, data contracts, platform consolidation, embedded ML, unusual problem framings.

## Operational Analytics

1. "Our operations team needs to see warehouse throughput, order fulfillment rates, and shipping delays updated every 15 minutes on a wallboard display."

2. "We need to correlate network outage events with customer support ticket volume to quantify the business impact of infrastructure failures."

3. "Our SLA monitoring is reactive — we find out we missed a target after the reporting period ends. We need proactive breach prediction."

4. "We want to detect capacity bottlenecks in our data centers by correlating CPU, memory, disk IO, and network utilization trends."

5. "Our NOC team needs a single dashboard that combines application metrics, infrastructure health, and business KPIs to triage incidents."

## Data Quality Automation

6. "Data quality checks run after the ETL completes, which means bad data sits in the warehouse for hours before it's flagged. We want inline validation."

7. "We need great expectations-style data contracts between our data producers and consumers with automated alerting on violations."

8. "Null values in the customer email field caused our entire marketing automation to send emails to 'null@company.com' last week."

9. "Our golden record for customers is computed from four source systems, but the merge logic has bugs that create phantom duplicates."

10. "We need schema evolution support — when a source adds a new column, it should flow through automatically without breaking existing queries."

## Platform Consolidation

11. "We have Tableau for BI, Jupyter for data science, and custom Python scripts for ETL. We want to consolidate into fewer tools."

12. "Our data infrastructure bill includes seven different SaaS subscriptions that overlap in functionality. We need to rationalize."

13. "Three different teams independently built Kafka-based streaming pipelines. We need to consolidate them into a single shared platform."

14. "We're paying for both a data warehouse and a data lake. Can we combine them into a single lakehouse architecture?"

15. "Our monitoring stack has Datadog for infrastructure, Grafana for custom dashboards, and PagerDuty for alerting. The data between them doesn't connect."

## Embedded ML Serving

16. "The fraud scoring model needs to evaluate every transaction at the point of sale within 50 milliseconds including network round trip."

17. "Our search relevance model needs to re-rank results based on user context, query intent, and personalization signals before returning results."

18. "We want to deploy edge ML models on our factory floor cameras that detect defects without sending video to the cloud."

19. "The pricing algorithm needs to consider real-time competitor data, current inventory levels, and demand elasticity curves."

20. "Our chatbot needs to retrieve relevant knowledge base articles, generate a contextual response, and check it against our policy guardrails."

## Data Strategy & Governance

21. "We need a data governance council but we're not sure who should be on it, what decisions they should make, or how to measure success."

22. "Our data catalog has 50,000 entries but only 2% have descriptions. Nobody maintains the metadata."

23. "We want to implement data mesh principles but our organization isn't structured around domains yet."

24. "The chief data officer wants a maturity assessment of our data capabilities across collection, storage, processing, analytics, and governance."

25. "We need a data retention policy that balances regulatory requirements, storage costs, and analytical value."

## Conversational & Frustrated

26. "I've been asking for a dashboard for six months and the BI team keeps telling me it's in the backlog. Meanwhile I'm making decisions blind."

27. "Our data warehouse project is three years old and we're still on phase one. The scope keeps growing and nothing ships."

28. "We bought Databricks but nobody knows how to use it. The vendor training was useless and our team is stuck."

29. "The previous data architect designed everything around their pet technology and now that they've left, nobody understands the architecture."

30. "Every time we hire a new data engineer, they want to rewrite everything in their preferred stack. We need architectural standards."

## IoT & Edge Computing

31. "Our connected vehicle fleet generates 2TB of telemetry data per day. We need to process it at the edge and only send anomalies to the cloud."

32. "Smart building sensors report temperature, humidity, CO2, and occupancy every 30 seconds across 200 buildings."

33. "Industrial PLCs on our manufacturing line produce measurements at 1000Hz. We need to downsample for analytics but keep full resolution for root cause analysis."

34. "Wearable devices for our clinical trial participants transmit heart rate, activity, and sleep data continuously. We need near-real-time adverse event detection."

35. "Agricultural sensors in remote locations have intermittent connectivity. Data arrives out of order and with gaps that need to be handled gracefully."

## Terse Technical

36. "ETL to ELT migration."

37. "Slowly changing dimensions Type 6."

38. "Federated query across heterogeneous sources."

39. "Streaming deduplication with exactly-once."

40. "Materialized view refresh strategy."

## Data Monetization & Sharing

41. "We want to publish curated datasets to external partners through a secure data sharing marketplace with usage tracking."

42. "Our data is a strategic asset that other business units want to consume. We need a data-as-a-product model with SLAs."

43. "We need to share anonymized aggregate data with academic researchers without exposing individual-level records."

44. "Clients are asking for API access to their own analytics data. We need a multi-tenant analytics API."

45. "Our industry consortium wants to build a shared data repository where members contribute data and get benchmarking insights back."

## Implicit Architecture Signals

46. "The marketing team runs campaigns and wants to know within an hour whether they're working, not wait for the weekly report."

47. "Our supply chain has 500 suppliers and we need to predict which ones will have delivery disruptions based on external signals."

48. "Finance closes the books on the third business day. Any data arriving after that needs to go into the next period with proper accrual adjustments."

49. "Customer behavior is different on mobile versus desktop and we need to analyze both channels together with consistent attribution."

50. "Our research dataset is 50TB and growing. Scientists need to run ad-hoc queries that scan the full dataset in under 10 minutes."
