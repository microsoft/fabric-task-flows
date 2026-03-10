# Problem Statements for Stress Testing

> Auto-generated batch 14 — 50 problems for self-healing loop. Focus: data lakehouse, change data capture, data observability, platform migration, cost management, embedded analytics, data privacy engineering.

## Change Data Capture & Sync

1. "When records change in our operational database, we need those changes reflected in the analytics layer within minutes, not hours."

2. "Our CDC pipeline captures inserts and updates but misses deletes, causing ghost records in the data warehouse that inflate our customer count."

3. "We need to replicate changes from five PostgreSQL databases into a central store while preserving the exact order of operations."

4. "The current replication lag is 4 hours, which means our customer service agents are looking at stale account information."

5. "We want to capture every field-level change to audit-sensitive tables so we can reconstruct the complete edit history."

## Data Observability & Monitoring

6. "We have no idea when data quality degrades until someone complains about a wrong number in a report."

7. "Pipeline failures are detected by downstream consumers, not by the pipeline itself. We need proactive monitoring."

8. "We want to track data freshness, volume, schema changes, and distribution shifts automatically across all our datasets."

9. "Last month a silent schema change in the source system caused three weeks of incorrect aggregations before anyone noticed."

10. "Our data team needs the equivalent of application monitoring but for data — something that pages us when data goes off the rails."

## Embedded & Operational Analytics

11. "We want to embed interactive charts directly into our SaaS product so customers can explore their own data without leaving the application."

12. "Our field service app needs to show technicians a predictive maintenance score for each asset they're servicing, calculated from the latest sensor data."

13. "Business users want natural language querying — they want to type a question and get an answer, not learn SQL."

14. "The product team wants to add a recommendation carousel to the homepage that updates based on browsing behavior within the current session."

15. "We need white-labeled analytics dashboards that each client can customize with their own branding and data filters."

## Cost Optimization & FinOps

16. "Our cloud data platform bill tripled in the past year and we have no visibility into which teams or workloads are driving the cost."

17. "Development and testing environments are running 24/7 but they're only used during business hours. We're wasting 67% of that spend."

18. "We need to implement chargeback so each business unit pays for their actual data platform consumption."

19. "The analytics warehouse automatically scales up during peak hours but it never scales back down — someone forgot to set the auto-pause."

20. "We're paying for hot storage on data that hasn't been queried in two years. We need a tiered storage strategy."

## Privacy Engineering

21. "We need to implement differential privacy for our customer analytics so that individual records can't be reverse-engineered from aggregate queries."

22. "Marketing wants to analyze customer behavior across brands but we can't share raw data between business entities due to consent boundaries."

23. "The data science team needs access to production-quality data but we can't give them real customer records. We need synthetic data generation."

24. "Our anonymization pipeline strips PII but the data team showed that combining zip code, birth year, and gender can still identify individuals."

25. "We need a clean room environment where two organizations can run joint analytics on combined datasets without either party seeing the other's raw data."

## Technical Debt Scenarios

26. "We have 200 stored procedures that nobody understands anymore. The original developer left three years ago and there's no documentation."

27. "Our ETL tool is end-of-support next year and we need to migrate 150 jobs to a modern platform without disrupting daily operations."

28. "The data model was designed for a completely different business five acquisitions ago. Nothing maps cleanly to our current organizational structure."

29. "We have three copies of the customer table in three different databases, each slightly different, and all three are considered the source of truth by different teams."

30. "Our test environment has synthetic data that's so different from production that tests pass but production fails regularly."

## Stress Tests (Ultra-Short)

31. "Ingestion bottleneck."

32. "Query performance."

33. "Access denied."

34. "Data silos."

35. "Late-arriving data."

## Hybrid & Multi-Cloud

36. "We run workloads on both Azure and AWS. Our analytics needs to span both clouds without duplicating all the data."

37. "Some datasets must stay on-premises for regulatory reasons but our analytics platform is in the cloud. We need a hybrid architecture."

38. "We're evaluating whether to consolidate on one cloud provider or maintain a multi-cloud strategy. What are the tradeoffs for our data platform?"

39. "Our disaster recovery plan requires that we can spin up the entire analytics platform in a secondary region within 4 hours."

40. "We need to federate queries across a cloud data warehouse and an on-premises SQL Server without moving the data."

## Real-World Messy Scenarios

41. "Half our data is in spreadsheets on people's desktops, the other half is in a CRM that only exports in XML, and the CEO wants a unified customer view by next quarter."

42. "We inherited three companies' data systems in the merger. Each has its own customer ID scheme, different product categorizations, and incompatible fiscal calendars."

43. "Our main database is a 15-year-old Access database that the entire accounting department depends on. We need to modernize without breaking their workflows."

44. "The marketing team signed up for a new analytics vendor last week without telling IT. Now we have data flowing to a system nobody in engineering knows how to manage."

45. "We discovered that 30% of our customer email addresses are invalid, 15% of phone numbers are duplicates, and our address data has four different formats."

## Meta-Questions

46. "How do we build a data platform that will still be relevant in five years?"

47. "What's the minimum viable data stack for a company that just hit product-market fit and is starting to scale?"

48. "When does it make sense to stop building in-house and just buy a platform?"

49. "How do we convince the board that investing in data infrastructure has ROI when the returns aren't immediately visible?"

50. "What's the most common mistake companies make when building their first data platform?"
