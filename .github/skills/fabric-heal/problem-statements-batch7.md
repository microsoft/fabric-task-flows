# Problem Statements for Stress Testing

> Auto-generated batch 7 — 50 problems targeting migration scenarios, team capability gaps, cost optimization, edge-to-cloud, and data platform maturity.

## Vague — Frustration-Driven

1. "Our data team quit and we're left with their mess."

2. "We spent $2M on a platform and nobody uses it."

3. "The vendor locked us in and now we're stuck."

4. "Our dashboards load so slowly nobody bothers looking at them."

5. "We can't hire data engineers — there aren't enough of them."

6. "Every department bought their own tool and now nothing integrates."

7. "Our data is stale by the time anyone sees it."

8. "We got fined for a data breach and need to fix everything."

9. "The project was supposed to take six months and it's been two years."

10. "We need to cut our data infrastructure costs in half without losing any capability."

## Semi-Detailed — Platform & Migration

11. "We have an on-prem Hadoop cluster that's end of life. The vendor stopped support and our Hadoop engineers have all left. We need to move 500TB of data to a modern platform without disrupting the 200 daily jobs that depend on it."

12. "Our Informatica ETL licenses cost $3M per year and renewal is coming up. We want to evaluate whether we can replace it with an open-source or cloud-native alternative without breaking 2,000 existing mappings."

13. "We run Teradata for our enterprise data warehouse but query performance has degraded as data volume grew. Most queries now take 20 minutes. Our analysts need sub-minute response times on ad-hoc queries against 10TB of data."

14. "Our company uses Snowflake for analytics but our data engineering team builds everything in Databricks. We need to decide whether to consolidate on one platform or maintain both. The politics are intense because each team is entrenched."

15. "We migrated to the cloud last year but our costs are 3x what was projected. We have 500 pipelines running 24/7 and most of them process data that nobody queries. We need to identify which pipelines are actually valuable and shut down the rest."

16. "Our legacy reporting system generates 5,000 reports per month. We surveyed users and found that only 300 are actually read. We want to sunset the unused reports but nobody knows which downstream processes might depend on them."

17. "We need to move from Oracle Database to PostgreSQL for cost reasons. Our application has 50,000 lines of PL/SQL stored procedures and 500 Oracle-specific features. We need to assess migration complexity and find a path forward."

18. "Our Tableau Server has 2,000 workbooks and 500 data sources. Performance is terrible and governance is nonexistent. Half the workbooks are broken or abandoned. We want to migrate to a modern BI platform but can't afford a big-bang cutover."

19. "We're running SAP HANA for analytics but the licensing costs are unsustainable. We want to offload analytical workloads to a cheaper platform while keeping SAP as the system of record for transactional data."

20. "Our startup grew fast and we've been storing everything in a single PostgreSQL database. It's now 5TB and queries are timing out. We need to separate analytical workloads from transactional without re-architecting our entire application."

## Detailed — Multi-System Complexity

21. "We're a global bank with operations in 40 countries. Each country has its own core banking system, regulatory reporting requirements, and data retention laws. We need a global risk analytics platform that can query across all countries' data without moving it — federated queries that respect data sovereignty. Our risk models need real-time market data feeds plus historical position data going back 10 years. Basel III/IV compliance reporting must be automated and auditable."

22. "Our media conglomerate owns 5 TV networks, 20 streaming services, and 50 digital publications. Each property has its own analytics stack measuring different things differently. We need unified audience measurement across all properties — a single person watching our content on TV, then streaming, then reading articles should be recognized as one individual. Privacy regulations (GDPR, CCPA) require consent-based tracking and the ability to honor opt-out requests across all platforms within 24 hours."

23. "We operate 500 fast-food restaurants with a franchise model. Each location has a POS system, kitchen display system, drive-through timer, and mobile order integration. We need real-time sales monitoring for corporate, predictive demand models for each location's prep quantities, crew scheduling optimization based on predicted traffic, and food safety temperature monitoring in walk-in coolers. Franchisees are independent operators who resist corporate oversight."

24. "Our pharmaceutical company conducts post-market surveillance on 50 approved drugs. We need to ingest adverse event reports from the FDA FAERS database, European EudraVigilance, social media mentions of side effects, and electronic health record data from partner health systems. Signal detection algorithms need to identify safety concerns earlier than traditional methods. Every detected signal must be evaluated within 15 calendar days per FDA requirements. Our pharmacovigilance team is 12 people monitoring all 50 drugs."

25. "We're a renewable energy company operating wind, solar, and battery storage assets across 100 sites. Each asset type has different monitoring systems and data formats. We need a unified asset performance management platform showing capacity factor, availability, revenue per MWh, and maintenance cost across all technologies. Grid operators send us curtailment signals that require immediate response — we need to adjust output within 4 seconds of receiving a dispatch instruction."

26. "Our e-commerce marketplace has 100,000 sellers and 50 million products. Product data quality is terrible — inconsistent categories, missing attributes, duplicate listings, and counterfeit product detection needs. We need automated product data enrichment using image recognition and NLP, duplicate detection using fuzzy matching, and a seller quality scoring system. Search relevance depends on having clean product data. Our catalog team of 20 can't manually review 50 million listings."

27. "We manage a national park system with 60 parks covering 25 million acres. We collect data from wildlife cameras, water quality sensors, visitor counters, weather stations, fire detection systems, and ranger patrol logs. We need predictive wildfire models, visitor capacity management, endangered species population tracking, and climate change impact analysis comparing multi-decade trend data. Rangers in the field use satellite phones with extremely limited bandwidth."

28. "Our automotive OEM receives telematics data from 2 million connected vehicles. Each vehicle reports location, speed, engine diagnostics, battery health, and driving patterns every 30 seconds when in motion. We need fleet-wide quality analytics to detect emerging defect patterns before they become recalls, predictive maintenance alerts pushed to vehicle owners' apps, and anonymized traffic pattern data sold to city planning agencies. Connected car data is subject to automotive privacy regulations in each market."

29. "We're a contract logistics provider handling returns processing for 100 retail clients. Each client has different return policies, grading criteria, and disposition rules. We need to track each returned item through receiving, inspection, grading, refurbishment, and disposition (restock, liquidate, recycle, or destroy). Processing time SLAs are 48 hours but we're averaging 5 days. We need to identify bottlenecks, predict daily return volumes per client, and optimize staffing."

30. "Our investment bank's compliance department needs to monitor all communications — emails, chat messages, voice calls, and video meetings — for 5,000 employees to detect insider trading, market manipulation, and conflicts of interest. We process 10 million messages per day. Pattern detection must identify subtle signals like unusual after-hours communication with counterparties, coded language, and sentiment shifts. Everything must be retained for 7 years and be searchable for SEC examination requests."

## Edge Cases — Competing Priorities

31. "We want real-time insights but our budget only supports batch processing infrastructure."

32. "Our data scientists want complete freedom to use any tool. Our security team wants to lock everything down. We need to satisfy both."

33. "We need to share data with 50 external partners but each partner should only see the data relevant to their region and product line."

34. "Our CEO wants all decisions to be data-driven within 6 months. We don't even have a data warehouse yet."

35. "We need to comply with 15 different regulatory frameworks simultaneously — some contradict each other on data retention periods."

36. "Our most critical insights come from combining data that's owned by three different business units, and none of them want to share."

37. "We want to retire our legacy system but 500 downstream consumers depend on its exact output format, including quirks and bugs they've come to rely on."

38. "Our European subsidiary generates data under GDPR, our US operations under CCPA, and our Asian operations under each country's local privacy law. We need unified analytics across all regions without violating any jurisdiction's requirements."

39. "We collect 10TB per day but only 1% of it is ever queried. We don't know which 1% in advance."

40. "We need our analytics to work offline when internet connectivity drops — our operations are in remote areas with unreliable connections."

## Rapid-Fire — One-Liners with Implicit Tech Signal

41. "We need real-time fraud detection but our systems are all batch."

42. "Our models are biased and we need to fix them before the regulator notices."

43. "Every query against our data lake takes 45 minutes."

44. "We have 100 data sources and no way to find what we need."

45. "Our pipelines fail silently and nobody notices until a report is wrong."

46. "We need to serve personalized recommendations to 50 million users in under 200ms."

47. "Our analysts can't write SQL so they ask the data team for everything."

48. "We process payments and need to detect money laundering in real-time."

49. "Our board wants a single number that represents the health of the company."

50. "We need to train ML models on data we're not allowed to centralize."
