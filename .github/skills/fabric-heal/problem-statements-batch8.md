# Problem Statements for Stress Testing

> Auto-generated batch 8 — 50 problems targeting regulatory urgency, ROI pressure, executive stakeholder requests, technical debt, and ambiguous requirements.

## Vague — Executive Requests

1. "I need a number I can put in front of the board tomorrow."

2. "We need to prove ROI on our data investments or the budget gets cut."

3. "Our competitor just launched an AI feature and our CEO wants one too."

4. "The auditor is coming next month and we're not ready."

5. "We need to reduce headcount by 20% using automation."

6. "My boss wants a digital transformation strategy by end of quarter."

7. "We got acquired and the parent company wants all our data in their format by March."

8. "Our biggest client threatened to leave because our reporting is unreliable."

9. "Regulators are changing the rules and we have 90 days to comply."

10. "We need to justify keeping our data team — show me the value they create."

## Semi-Detailed — Technical Debt

11. "We have 2,000 stored procedures in our SQL Server database. Some of them were written 15 years ago by people who no longer work here. Nobody knows what half of them do, but we're afraid to touch them because downstream reports might break."

12. "Our ETL pipelines have no error handling. When a source system changes its schema — which happens every few months — everything breaks and it takes a week to figure out which pipeline was affected."

13. "We built a data warehouse 10 years ago following Kimball methodology. It works great for known reporting patterns but it's terrible for ad-hoc exploration. Adding a new dimension takes a sprint of development."

14. "Our microservices architecture means data is scattered across 200 databases. There's no central place to understand the full state of an order that touches 12 different services."

15. "We have 50TB of logs that we're paying to store but we have no search or analytics capabilities on them. When there's an incident, engineers grep through log files on individual servers."

16. "Our CI/CD pipeline tests code changes but doesn't test data pipeline changes. We've had three incidents this quarter where a schema change in a source system broke our downstream analytics without anyone knowing until the weekly report was wrong."

17. "We have a Kafka cluster processing 500,000 messages per second but our consumers can't keep up. Back-pressure is causing message lag that's growing by 2 hours every day. We need to either speed up processing or prioritize which messages to process first."

18. "Our data lake is 2PB and growing 10% per month. Storage costs are $50K per month. We know most of the data is never accessed but we can't identify which data is actively used versus abandoned."

19. "Our APIs serve 10 million requests per day but we have no analytics on API usage patterns. We don't know which endpoints are most used, which clients are consuming the most resources, or whether our SLAs are actually being met."

20. "We migrated to the cloud but kept the same architecture — we essentially lifted and shifted our on-prem problems. Our cloud costs are now 5x our old on-prem costs and performance is actually worse."

## Detailed — Domain-Specific Complexity

21. "Our airline needs to comply with new EU passenger rights regulations requiring automated compensation processing when flights are delayed more than 3 hours. We need to automatically detect qualifying delays from our operations data, calculate compensation amounts based on route distance and delay duration, initiate payments through our finance system, and maintain a complete audit trail. We process 200,000 flights per month and the regulation takes effect in 90 days."

22. "Our pharmaceutical distribution company handles controlled substances (Schedule II-V). The DEA requires suspicious order monitoring — we need to detect unusual ordering patterns in real-time and file suspicious order reports within 1 business day. Each order must be validated against the customer's license, order history, and threshold limits. We process 50,000 orders per day from 15,000 customers."

23. "Our power grid operator needs a next-generation energy management system. We have 50,000 substations with SCADA telemetry at 4-second intervals, weather forecast feeds, renewable generation forecasts (solar and wind are intermittent), demand response program signals, and wholesale energy market prices updating every 5 minutes. We need load forecasting accurate to 1% for the next 48 hours, real-time congestion management, and automated dispatch of generation resources."

24. "Our autonomous drone delivery startup needs to process flight telemetry from 100 drones operating simultaneously in urban environments. Each drone streams GPS, altitude, battery level, camera feeds, and obstacle detection data at 100Hz. We need real-time collision avoidance coordination, delivery route optimization considering weather and airspace restrictions, battery management predictions, and FAA-mandated flight logging with 90-day retention."

25. "Our clinical trial management company runs decentralized trials where patients use wearable devices and mobile apps from home. We collect continuous heart rate, blood oxygen, activity data, patient-reported outcomes via surveys, and medication adherence tracking. We need real-time safety monitoring for adverse events, data quality dashboards for sponsors, protocol deviation detection, and eCRF data integration. FDA 21 CFR Part 11 compliance required."

26. "Our municipal water authority needs to optimize chemical treatment dosing in real-time. We monitor raw water quality parameters — turbidity, pH, alkalinity, temperature, organic carbon — at the intake every 30 seconds. Treatment chemical costs are $5M annually and we believe optimal dosing could save 20%. We need predictive models for finished water quality based on raw water characteristics and treatment parameters, while maintaining compliance with Safe Drinking Water Act standards."

27. "Our space agency manages a constellation of 50 satellites. Each satellite downlinks telemetry during 8-minute ground station passes — housekeeping data, payload science data, and orbital parameters. We need automated health assessment during the contact window, anomaly detection comparing current telemetry to historical baselines, collision avoidance analysis using TLE data from Space Force, and mission planning optimization for observation scheduling."

28. "Our fashion retailer needs demand sensing that incorporates social media trend detection, search query volume, weather forecasts, and competitor pricing. Fashion lifecycles are 6-8 weeks — by the time traditional forecasting methods react, the trend is over. We need to detect emerging trends 2-3 weeks before they peak and automatically adjust purchase orders. Our supply chain from design to store shelf is 4 weeks."

29. "Our nuclear power plant generates 10,000 process measurements per second from reactor instrumentation, safety systems, and balance-of-plant equipment. NRC regulations require us to retain all safety-related data for the lifetime of the plant (40+ years). We need to detect equipment degradation patterns, optimize maintenance outage planning, and generate regulatory performance reports. All systems must be cyber-security hardened per 10 CFR 73.54."

30. "Our genomics lab processes 1,000 whole genome sequences per week, each generating 100GB of raw data. Bioinformaticians need to run variant calling pipelines, compare variants against reference databases (ClinVar, gnomAD), and generate clinical reports for physicians. Turnaround time SLA is 2 weeks from sample receipt to report. Data must be stored in a CLIA-certified environment with full chain of custody."

## Edge Cases — Contradiction & Ambiguity

31. "We want AI everywhere but our data quality is terrible."

32. "We need everything to be real-time but we can't afford to re-architect our batch systems."

33. "We want complete data transparency with our customers but we also need to protect our proprietary analytics."

34. "We need to reduce our data footprint by 80% but we also need to keep everything for compliance."

35. "Our users want instant answers but our data pipeline has a 6-hour lag."

36. "We need enterprise-grade security and governance but we also need data scientists to move fast and experiment freely."

37. "We want to consolidate all our data but some divisions have contractual obligations to keep their data in separate systems."

38. "We need to support 10,000 concurrent users on our analytics platform but our budget is $10K per month."

39. "Our data needs to be both highly available and perfectly consistent — we know we can't have both, but the business insists."

40. "We want predictive analytics but our historical data only goes back 6 months."

## Rapid-Fire — Clear Tech Signal, Terse Phrasing

41. "Need real-time dashboards from streaming data."

42. "Migrate 500 tables from Oracle to cloud."

43. "Build a recommendation engine for our mobile app."

44. "Automate our compliance reporting — SOX, GDPR, and HIPAA."

45. "Detect anomalies in our IoT sensor data within 30 seconds."

46. "Build a customer 360 from 12 different source systems."

47. "We need to query petabytes of historical data interactively."

48. "Set up a feature store for our ML models."

49. "Ingest and process 1 million events per second."

50. "Create a self-service analytics portal for business users."
