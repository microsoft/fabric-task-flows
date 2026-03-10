# Problem Statements for Stress Testing

> Auto-generated batch 4 — 50 problems at varying depth (vague, semi-detailed, detailed) for self-healing loop.

## Batch A — Ultra-Vague (One-liners, minimal tech signal)

1. "We have too much data and not enough answers."

2. "Things are falling through the cracks."

3. "Our team can't agree on the numbers."

4. "We need a single pane of glass."

5. "Everything is in spreadsheets and it's a mess."

6. "We don't know what we don't know."

7. "Our data is everywhere."

8. "Help us make sense of all this information."

9. "We're flying blind."

10. "Our reports are always wrong."

## Batch B — Semi-Detailed (Some tech signal, implicit intent)

11. "We collect data from dozens of systems but nobody trusts the numbers because they never match. Sales says revenue is one thing, finance says another."

12. "Our field technicians fill out paper forms and fax them back to the office. By the time the data is entered, it's two weeks old and useless for planning."

13. "We run a 24/7 operation and when something goes wrong at 3am, nobody notices until the morning shift arrives and sees the damage."

14. "Our customers call our support line and the agent has to check five different systems to get a complete picture of their account."

15. "We inherited three companies through acquisitions and now we have three of everything — three CRMs, three ERPs, three data warehouses. Nothing talks to each other."

16. "We have petabytes of historical data sitting in on-prem storage that nobody can query because it takes hours to run even simple reports."

17. "Our compliance team manually checks every transaction against a spreadsheet of sanctioned entities. It takes 40 people and they still miss things."

18. "Management wants a dashboard by Friday showing how we're doing. The problem is 'how we're doing' means different things to every executive."

19. "We sell through 50 channel partners and have no visibility into sell-through data until 60 days after the quarter ends."

20. "Our engineers spend 80% of their time cleaning data and 20% doing actual analysis. We want to flip that ratio."

## Batch C — Detailed Technical Problems

21. "Our e-commerce platform generates 10 million clickstream events per hour. We pipe these through a message queue but our batch analytics pipeline only processes them once daily. Marketing wants to see campaign performance within 15 minutes of a promotion launch, but our data science team needs the full day's data for attribution modeling. We need both velocities in one architecture."

22. "We operate 200 connected vending machines across 50 locations. Each machine reports inventory levels, transaction data, and temperature readings every 5 minutes. We want to predict when machines will run out of popular items and dispatch restocking crews proactively. Currently dispatchers wait for empty-machine alerts and respond reactively."

23. "Our legal department has 50,000 contracts stored as PDFs across SharePoint, network drives, and email attachments. We need to extract key clauses — termination, indemnification, auto-renewal — classify risk level, and build a searchable repository. Attorneys want to ask natural language questions like 'show me all contracts with unlimited liability' and get instant answers."

24. "We're a subscription business with 2 million subscribers. We have data in Stripe for billing, Segment for product analytics, Zendesk for support, and HubSpot for marketing. Each tool has its own customer ID. We need to build a unified customer profile, calculate health scores, and trigger automated workflows — like pausing billing when a customer opens a P1 support ticket."

25. "Our manufacturing plant has 50 PLCs generating 100,000 data points per second. We log everything to a historian database. Quality engineers want to correlate product defects found in inspection with process parameters from the exact time window that part was being made. Right now this takes 3 days of manual SQL queries."

26. "We receive feeds from 30 external data vendors — some push via SFTP drops every hour, some expose REST APIs, some send email attachments. Data formats include CSV, XML, JSON, and proprietary binary formats. We need to normalize everything into a common schema, validate data quality, and make it queryable within 2 hours of receipt."

27. "Our hospital generates 5TB of DICOM imaging data per month — MRIs, CT scans, X-rays. Radiologists annotate findings in their reports. We want to build an AI training pipeline that pairs images with annotations, train diagnostic models, and deploy them back to the PACS system for real-time read assist. All data must remain within our HIPAA-compliant enclave."

28. "We run a loyalty program across 500 retail stores. Members earn points on purchases and redeem them for rewards. Our current system can't handle real-time point balance updates during peak shopping periods — Black Friday we had 30-minute delays in point accrual. Members expect instant gratification."

29. "Our fleet of 1,000 delivery vehicles has dashcams that record continuously. We want to analyze driving behavior — hard braking, speeding, following distance — to create driver safety scores. Each vehicle generates 50GB of video per day. We can't send all of that to the cloud; we need edge processing with only events and metadata sent centrally."

30. "We publish 200 regulatory filings per year to SEC, FINRA, and state regulators. Each filing requires data from 15 internal systems, 3 external data providers, and approval workflows involving 20 people. The average filing takes 6 weeks to prepare. We need to automate data collection, reconciliation, and formatting while maintaining full audit trail for examiner review."

## Batch D — Tricky Mixed-Signal Problems

31. "We have 10,000 IoT sensors in our buildings measuring temperature, humidity, and CO2. But we also need monthly energy reports for our board and quarterly sustainability disclosures for investors. The sensor data is useful for both real-time comfort alerts and long-term trend analysis."

32. "Our call center handles 50,000 calls per day. We transcribe every call using speech-to-text. We want real-time agent coaching that suggests responses during the call, plus batch analytics on call topics and sentiment trends for weekly management reviews."

33. "We're a marketplace connecting 10,000 sellers with 5 million buyers. Sellers need real-time pricing recommendations based on competitor data, but we also need weekly marketplace health reports showing GMV, take rate, and seller satisfaction. Fraud detection needs to happen on every transaction instantly."

34. "Our research lab generates 100GB of experimental data per day from DNA sequencers, mass spectrometers, and electron microscopes. Scientists need interactive notebooks to explore this data, but we also need a data catalog so researchers can discover and reuse datasets across projects."

35. "We collect customer feedback from surveys, social media, support tickets, app store reviews, and NPS scores. We want real-time alerting when sentiment drops, but also quarterly voice-of-customer reports synthesizing all channels. The C-suite wants a single metric — not five different dashboards."

36. "Our trading desk needs sub-second access to market data for algorithmic strategies, but our risk team needs end-of-day position reports aggregated across all desks. Same data, different velocities, different consumers."

37. "We're a media company that monetizes content through both subscriptions and advertising. We need real-time ad impression tracking for yield optimization, but our finance team needs monthly revenue recognition reports that reconcile subscription and ad revenue. These two systems currently don't share data."

38. "Our smart grid has 2 million smart meters reporting every 15 minutes, plus weather forecast feeds updating hourly. We need real-time outage detection when meters go silent, predictive load forecasting for tomorrow's grid operations, and historical consumption analytics for rate case filings with the utility commission."

## Batch E — Problems That Emphasize Governance/Quality

39. "We have 500 Power BI reports and nobody knows which ones are still accurate. Reports reference the same metrics but show different numbers."

40. "Our data engineering team builds pipelines but there's no documentation. When someone leaves, their pipelines become black boxes."

41. "Three departments define 'active customer' differently. Sales counts anyone who logged in this month. Marketing counts anyone who opened an email. Finance counts anyone who paid."

42. "We need to implement data access controls — our HR data, financial data, and customer data all sit in the same lakehouse but different teams should only see what's relevant to them."

43. "Our data lake has grown to 500TB but 60% of it is duplicate, stale, or undocumented data that nobody uses. We're paying storage costs for data we can't even identify."

44. "We're implementing a data mesh but teams can't agree on how to define and publish data products. Everyone has their own definition of key entities like 'customer', 'order', and 'product'."

45. "Every time we onboard a new data source, it takes 3 months because there's no standardized ingestion framework. Each engineer builds their own pipeline from scratch."

46. "Our auditors flagged us because we can't demonstrate data lineage — we can't trace a number in a board report back to the source transaction that produced it."

47. "We merged with a competitor and now have two completely separate data platforms. Both need to keep running while we figure out the migration plan. Users from both companies need access to a unified view."

48. "Our machine learning models are in production but we have no monitoring. We don't know if predictions are drifting, if input data quality is degrading, or if models are being used at all."

49. "We have sensitive PII scattered across 200 databases and we don't even know where all of it is. We need to discover, classify, and protect it before our GDPR audit in 3 months."

50. "Our BI team gets 200 ad-hoc data requests per month. Most are variations of the same questions but asked differently. We want to enable self-service analytics but our data is too messy for business users to query directly."
