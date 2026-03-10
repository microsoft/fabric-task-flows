# Problem Statements for Stress Testing

> Auto-generated batch 11 — 50 problems for self-healing loop. Focus: migration edge cases, operational bottlenecks, platform consolidation, emerging workload patterns, passive voice, indirect phrasing.

## Migration & Modernization

1. "Our legacy system stores everything in a single Oracle database that hasn't been upgraded since 2018. We need to decompose it into purpose-built stores while keeping the lights on during transition."

2. "The mainframe batch jobs run every night but sometimes don't finish before business hours, causing cascading delays across downstream systems."

3. "We're moving off Teradata and need something that can handle our 50TB fact tables without breaking the bank on compute."

4. "Three different teams built three different data pipelines to solve the same problem. Now we have conflicting numbers and nobody trusts any of them."

5. "Our on-prem Hadoop cluster is end-of-life and we need a cloud migration path that preserves our existing Spark workloads."

## Operational Bottlenecks

6. "It takes our analysts two weeks to get a new dataset provisioned because they have to file a ticket, wait for DBA approval, and then someone manually creates the table."

7. "Every quarter-end, the finance team manually downloads CSV files from six different systems and spends three days reconciling them in Excel."

8. "Our data engineers spend 80% of their time firefighting broken pipelines instead of building new features."

9. "The overnight refresh keeps failing silently and nobody notices until the CFO asks why the dashboard numbers haven't changed."

10. "We have 400 reports but only 30 people actually look at them. Nobody knows which ones matter anymore."

## Scale & Performance Pressure

11. "Our API response times have degraded from 50ms to 800ms as the dataset grew from 1 million to 90 million records."

12. "The monthly aggregation job that used to take 2 hours now takes 14 hours and keeps timing out."

13. "We need to serve personalized recommendations to 10 million users with sub-second latency."

14. "Our search index rebuild takes 6 hours and during that window, customers see stale results."

15. "Peak traffic during product launches overwhelms our analytics pipeline and we lose event data."

## Data Governance & Trust

16. "We passed our last audit but the auditors flagged that we have no lineage tracking and warned us it won't fly next year."

17. "Different departments define revenue differently and the board gets confused when the numbers don't match across presentations."

18. "Our GDPR deletion process is manual — someone has to search five databases and three file shares to find all records for a single customer."

19. "We can't tell which version of the customer record is authoritative because it's been modified in four different systems."

20. "Sensitive employee data is being accessed by analysts who shouldn't have visibility into salary and performance review information."

## Passive & Indirect Phrasing

21. "It has been observed that data inconsistencies between the warehouse and the operational database are increasing month over month."

22. "A request has been made to explore options for reducing the time between data generation and its availability for analysis."

23. "The organization is considering whether a unified view of customer interactions would improve cross-selling opportunities."

24. "Concerns have been raised about the ability of current infrastructure to handle anticipated growth in connected device telemetry."

25. "An assessment is needed to determine whether existing data processing capabilities meet the requirements of upcoming regulatory changes."

## Aspirational & Strategic

26. "We want to become a data-driven organization but right now most decisions are made based on gut feeling and tribal knowledge."

27. "The CEO wants a single pane of glass that shows the health of every business unit in real time."

28. "Our competitors are using machine learning for dynamic pricing and we're still updating prices manually in spreadsheets."

29. "We need to democratize access to data so that business users can answer their own questions without waiting for the analytics team."

30. "Leadership wants to understand the total cost of data ownership across all our platforms and services."

## Multi-Signal Complex Scenarios

31. "Customer support calls are recorded and transcribed but nobody analyzes the text. We want to detect emerging product issues from call patterns before they become widespread."

32. "Our supply chain generates millions of sensor readings per day from warehouse temperature monitors, GPS trackers on trucks, and barcode scanners at loading docks. We need to predict delays before they happen."

33. "We collect clickstream data from our website, purchase history from our POS system, and email engagement metrics from our marketing platform. We want a unified customer profile that updates as interactions happen."

34. "Our R&D team runs experiments that generate terabytes of simulation data. They need to compare results across hundreds of parameter combinations and share findings with remote collaborators."

35. "We process insurance claims that arrive as scanned documents, emails with attachments, and structured API submissions. Each needs to be classified, extracted, validated against policy rules, and routed to the right adjuster."

## Ultra-Short & Vague

36. "Dashboards are slow."

37. "We need better data."

38. "Too many manual steps."

39. "Can't find anything."

40. "Data is everywhere."

## Question-Style Problems

41. "How do we make sure our analytics reflect what actually happened in the last hour instead of showing yesterday's data?"

42. "What's the best way to handle a situation where some data needs to be processed immediately and other data can wait until overnight?"

43. "Is there a way to automatically detect when a data pipeline produces results that look significantly different from historical patterns?"

44. "How should we structure our data so that adding new data sources doesn't require rebuilding everything from scratch?"

45. "What approach should we take when we need to combine structured transaction data with unstructured customer feedback?"

## Constraint-Heavy Scenarios

46. "We're regulated by SOX and HIPAA, process 2 million transactions daily, need 99.99% uptime, and have a total budget of $50K per month for our entire data platform."

47. "Our team is three people: one data engineer, one analyst, and one manager. We need to replace five manual reporting processes and add predictive capabilities."

48. "Everything must run in our private cloud — no public cloud services allowed — and we need to process streaming data from 10,000 edge devices."

49. "We have six months to demonstrate ROI or the project gets cancelled. The first deliverable needs to be visible within 30 days."

50. "The system must support both OLTP workloads for our customer-facing application and OLAP workloads for our analytics team, without them interfering with each other."
