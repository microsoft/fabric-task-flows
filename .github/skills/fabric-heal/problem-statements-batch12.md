# Problem Statements for Stress Testing

> Auto-generated batch 12 — 50 problems for self-healing loop. Focus: embedded analytics, edge inference, streaming joins, reverse ETL, data contracts, observability, platform engineering.

## Data Platform Engineering

1. "Our data platform team supports 15 product teams but every new integration takes a month because there's no self-service layer — everything goes through a central queue."

2. "We built our data lake three years ago but it's become a data swamp. Nobody can find anything and there's no catalog or documentation."

3. "Every time a source system changes its schema, three downstream pipelines break and nobody finds out until the morning standup."

4. "We want to implement data contracts so that producers and consumers have clear expectations about data shape, freshness, and quality."

5. "Our Spark cluster costs $40K/month but utilization is below 20%. We need to right-size or replace it with something more elastic."

## Reverse ETL & Activation

6. "We have great analytics in our warehouse but the insights never make it back to the operational systems where our sales team works."

7. "Marketing needs customer segments pushed into our CRM and email platform daily, but right now someone manually exports a CSV and uploads it."

8. "Our product team wants to use ML model scores in the application layer but there's no clean way to get predictions from the analytics environment into the production database."

9. "Customer success managers need churn risk scores visible in their ticketing system, not buried in a dashboard they never check."

10. "We calculate lifetime value in our warehouse but the e-commerce platform has no way to access it for personalization."

## Streaming & Event Processing

11. "Our payment processing system needs to validate transactions against fraud rules within 200 milliseconds or the payment gateway times out."

12. "We want to detect when a user abandons their shopping cart and trigger a notification within 5 minutes, not the next day via batch."

13. "Log events from 500 microservices need to be aggregated in real time so our SRE team can detect anomalies before customers notice."

14. "We need to join a stream of clickstream events with a slowly-changing dimension table of product categories to enrich the events in flight."

15. "IoT temperature readings need to be windowed into 30-second averages and any reading above the threshold should immediately trigger an alert."

## Unstructured Data Challenges

16. "We have 2 million PDF contracts stored in SharePoint. Legal wants to search across all of them for specific clauses and extract key terms."

17. "Customer reviews come in from six platforms in different languages. We need to aggregate sentiment and detect trending topics."

18. "Our help desk receives 500 tickets per day as free-text. We want to auto-categorize them and route high-severity issues to senior staff."

19. "Meeting recordings are transcribed but the transcripts just sit there. We want to extract action items and link them to project tracking."

20. "Engineering specs arrive as CAD drawings and technical PDFs. We need to extract dimensions, materials, and tolerances into a structured database."

## Compliance & Audit Readiness

21. "We need to prove to auditors exactly which transformations were applied to every number in the regulatory report, from source to final figure."

22. "Data retention policies require us to automatically delete records older than 7 years, but our deletion process hasn't been tested since it was built."

23. "We operate in 12 countries and each has different data residency requirements. We need to ensure data doesn't cross borders during processing."

24. "The compliance team manually reviews access logs quarterly, but they need near-real-time alerts when someone accesses sensitive tables."

25. "Our data masking solution only covers the production database but analysts have been querying copies of sensitive data in the sandbox environment."

## Conversational & Informal

26. "Honestly, we're drowning in data but starving for insights. Everyone has their own spreadsheet and nobody agrees on anything."

27. "The BI team is a bottleneck — every question takes two weeks to answer. By then the decision has already been made based on gut feeling."

28. "We tried a data lakehouse once and it was a disaster. Convince me why we should try again."

29. "My boss wants AI but I don't think we have the data foundation for it. What should we build first?"

30. "We keep buying tools but nothing talks to each other. We have Snowflake, Databricks, Power BI, and a bunch of Python scripts held together with duct tape."

## Cross-Domain Complex

31. "We run a marketplace where buyers and sellers interact. We need real-time pricing signals, fraud detection on transactions, recommendation engine for product discovery, and compliance reporting for tax purposes."

32. "Our fleet management system collects GPS pings every 10 seconds from 5,000 vehicles. We need route optimization, predictive maintenance alerts, fuel consumption analytics, and driver behavior scoring."

33. "We process clinical trial data that involves patient consent tracking, adverse event detection from unstructured notes, statistical analysis across cohorts, and regulatory submission packaging."

34. "Our digital advertising platform needs to process 100 million bid requests daily, match them against audience segments, track campaign attribution across channels, and report ROAS to advertisers within 6 hours."

35. "We manage a content platform where users upload videos, images, and documents. We need content moderation, recommendation algorithms, usage analytics, and royalty calculations for creators."

## Minimal & Ambiguous

36. "Reports take forever."

37. "Nobody trusts the numbers."

38. "Schema keeps changing."

39. "Need real-time but also history."

40. "Too expensive."

## Question-Format

41. "How do we version our datasets so that when a model was trained on last Tuesday's data, we can reproduce exactly what it saw?"

42. "What's the right approach when our batch window is shrinking and we're running out of time to process everything overnight?"

43. "Can we build a system where business users define their own metrics in plain English and get automatically generated dashboards?"

44. "How should we handle late-arriving data in a streaming pipeline without reprocessing everything?"

45. "Is it possible to test data pipelines the same way we test application code, with unit tests and integration tests?"

## Constraint-Heavy

46. "We're a 50-person startup with no dedicated data team. One backend engineer does everything data-related on Friday afternoons. We need basic analytics and a customer health dashboard."

47. "Everything must be open-source — no vendor lock-in. We need real-time dashboards, ML model serving, and automated data quality checks."

48. "Our data must never leave our VPC. We process 10TB daily, need sub-second query response times, and have a 3-person data team."

49. "We have a 90-day deadline to migrate from our current vendor before the contract expires. 200+ pipelines, 50+ dashboards, and 3TB of historical data."

50. "The board wants to see ROI in 6 weeks. We need to pick the one highest-impact use case and deliver an end-to-end solution that moves the needle."
