# Problem Statements for Stress Testing

> Generic data/analytics scenarios for testing agent pipeline inference. Intentionally vague — the system should ask clarifying questions to resolve ambiguity.

## Batch & Warehouse

1. "We have sales data in spreadsheets across 12 regional offices. Leadership wants a single dashboard they can check weekly."

2. "Our data warehouse is too slow. Queries that used to take seconds now take minutes. We're thinking about moving to the cloud."

3. "Finance exports CSVs from our ERP every night. We need to combine them with CRM data for quarterly reporting."

4. "We want to replace our on-prem data warehouse but can't afford downtime. Need a migration path that doesn't break existing reports."

5. "Marketing has 3 years of campaign data in flat files. They want self-service analytics but don't know SQL."

## Real-Time & Streaming

6. "Our IoT sensors generate temperature readings every 5 seconds. We need alerts when values exceed thresholds, plus daily trend reports."

7. "We're tracking website clickstream data and want to detect anomalies in real-time — like sudden traffic drops or bot activity."

8. "Delivery trucks send GPS pings every 30 seconds. Operations wants a live map plus historical route analysis."

9. "Our payment processing system needs fraud detection within 200ms of a transaction. Current batch approach catches fraud too late."

10. "Factory floor sensors stream vibration data. We want predictive maintenance alerts before equipment fails."

## Hybrid (Batch + Real-Time)

11. "We need both a real-time view of inventory levels and end-of-day reconciliation reports for accounting."

12. "Customer support tickets come in throughout the day, but we also need weekly sentiment analysis trends for the executive team."

13. "Our e-commerce site needs real-time stock updates while also feeding a nightly data warehouse for business intelligence."

## Analytics & ML

14. "We have 5 TB of customer transaction history. We want to build propensity-to-churn models but our data scientists spend 80% of their time on data prep."

15. "Marketing wants to predict which leads will convert. We have CRM data but no ML infrastructure."

16. "We're sitting on years of support ticket text. Someone said we could use AI to auto-categorize incoming tickets."

## Governance & Security

17. "We need to mask PII before analysts can query customer data. Currently it's all or nothing — either full access or no access."

18. "Auditors are asking for lineage reports. We can't tell them where a number in a dashboard actually came from."

19. "Different departments have their own data silos. We want a unified catalog but can't force everyone onto one platform."

## Vague / Ambiguous (Maximum Stress Test)

20. "We want to be more data-driven. Not sure where to start — we have data everywhere but no insights."

## Enterprise & Global Strategy

21. "We're a Fortune 500 with 40,000 employees across 28 countries. We have Snowflake for our North American analytics, Databricks in EMEA for data science, and a legacy Oracle data warehouse in APAC. The CEO wants a single global view of revenue, but nobody wants to give up their regional tools."

22. "Our conglomerate has 14 business units each with their own data teams, different tech stacks, different maturity levels. Corporate wants a federated data mesh but with centralized governance. Some units are on Azure, some AWS, two are still fully on-prem."

23. "We're a global bank. We need to consolidate risk analytics across 6 trading desks, each using different models and data sources. Regulatory reporting deadlines are non-negotiable — we can't break anything during the transition. We also need real-time position monitoring for the trading floor."

24. "Our healthcare system spans 200 hospitals. We need to unify clinical data for population health analytics while maintaining HIPAA compliance. Each hospital has its own EMR — some Epic, some Cerner, some home-grown. We also want to pilot an AI model for readmission prediction."

25. "We're an energy company managing a smart grid across 3 states. We have 2 million smart meters streaming consumption data, SCADA systems for grid operations, a legacy billing system on Oracle, and weather API feeds. We need demand forecasting, outage prediction, and a customer-facing usage dashboard — all from the same platform."

26. "We're a global retailer with 4,000 stores. We need customer 360 — combining POS transactions, loyalty program data, e-commerce clickstream, and social media sentiment. The marketing team wants real-time personalization for the website, the merchandising team wants weekly demand forecasting, and finance wants monthly P&L by store."

27. "Our manufacturing company has 12 plants worldwide. Each plant has its own historian database and SCADA system. We need a central operations dashboard showing real-time OEE across all plants, predictive maintenance for critical equipment, and monthly quality trend reports for the VP of Operations. The plants are on different time zones and some have spotty internet connectivity."

## Power BI Users Exploring Fabric

28. "I've been using Power BI Desktop for years. My boss said we're getting Fabric and I should move my reports there. I don't really understand what Fabric adds — my reports work fine. What's in it for me?"

29. "We have about 200 Power BI reports across the organization. Some use Import mode, some DirectQuery, and they're all over the place. Reports are slow, people complain, and we spend half our time managing gateway refreshes. Someone mentioned Direct Lake would fix everything?"

30. "I'm a Power BI developer. I know DAX and Power Query really well but I've never written Python or SQL. My manager wants me to start building lakehouses. I have no idea what a lakehouse even is or why I'd want one instead of just connecting Power BI to our SQL Server like I always have."

31. "We're a small analytics team — 3 people, all Power BI. We currently use Power BI Pro with shared datasets. Now IT is talking about Fabric capacities, workspaces, lakehouses, warehouses, notebooks — it feels like 10x the complexity for not much benefit. Can you help us understand if we even need Fabric?"

32. "Our Power BI reports pull from 15 different data sources — some Excel files, some SQL databases, some SharePoint lists, a couple of Dataverse tables. Every Monday morning the dashboards break because someone moved a file or changed a column name. We need something more reliable but we don't want to learn a whole new platform."

## Multi-Platform Integration

33. "We use Databricks for all our ML pipelines and it's working great. But our business users only know Power BI and they can't connect to Databricks easily. We don't want to move off Databricks — we just need a way to get the ML outputs into Power BI dashboards without manual CSV exports."

34. "We have a massive Snowflake investment — 500 TB, 200 users, years of dbt models. We're not migrating. But our board just mandated Microsoft 365 Copilot and they want it to be able to answer questions from our Snowflake data. How does Fabric fit in without replacing what we have?"

35. "Our data lives in MongoDB for the app, PostgreSQL for billing, and S3 for log archives. We've been duct-taping Python scripts to pull it all together for monthly reports. We need a real analytics layer but we're a startup with 4 engineers and no dedicated data team."

## Ambiguous Intent

36. "We just got a Fabric trial capacity. What should we build first? We have some data in Azure SQL and some Power BI reports already."

37. "Our competitor just announced an AI-powered analytics platform. Our CEO wants the same thing by Q3. We have data but no AI strategy, no ML engineers, and our analytics team is 2 people with Excel skills."

38. "We're migrating from AWS to Azure. Part of that is figuring out what to do about our Redshift data warehouse and the QuickSight dashboards connected to it. But honestly some teams want to keep using AWS for certain workloads."

39. "I was told Fabric replaces Synapse, Data Factory, and Power BI all in one. Is that true? We use all three today and I'm worried about what breaks if we switch. Also our Synapse workspace has a lot of Spark notebooks that took months to build."

40. "We need a data strategy. We've been collecting data for 10 years but nobody trusts it. Different teams have different numbers for the same KPIs. Before we build anything new, we need to figure out what data we actually have, who owns it, and which version is right."

## Telecom & Connectivity

41. "We operate a 5G network across 14 metropolitan areas with 8,000 cell sites. Each site generates RAN performance metrics — throughput, latency, handover success rates — every 10 seconds. Our NOC team needs real-time network health dashboards, but our capacity planning team needs 90-day trend analysis to decide where to add small cells. Currently the RAN data lands in Splunk and nobody can query it for planning purposes."

42. "Our MVNO billing platform processes 120 million CDR records per day from three upstream carriers. We reconcile these against our own rating engine outputs nightly, but discrepancies take 2 weeks to investigate because the data lives in 4 different Oracle databases. Finance wants a unified billing analytics view with drill-down to individual CDR mismatches, and they need it by end of quarter for the audit."

43. "We're a rural broadband ISP serving 200,000 subscribers across 6 states. Our DOCSIS 3.1 cable modems report signal quality metrics (SNR, power levels, uncorrectable codewords) via SNMP every 5 minutes. We want to predict modem failures before they cause outages, but our engineering team has 3 people and they only know SQL. We also need FCC Form 477 compliance reports quarterly."

## Insurance & Risk

44. "Our P&C insurance company processes 45,000 claims per year across auto, home, and commercial lines. Claims adjusters use Guidewire ClaimCenter, but our actuarial team exports data to SAS for loss reserving models. We need to unify the claims data pipeline so actuaries can run IBNR calculations on fresh data daily instead of monthly, while maintaining SOX compliance for all financial data transformations."

45. "We're building a parametric insurance product for crop damage. When NOAA weather stations report hail events exceeding specific thresholds, we need to automatically trigger claim payouts within 4 hours. The system needs to ingest real-time weather feeds, correlate with policyholder GPS coordinates, calculate damage estimates using our proprietary models, and push payout authorizations to our claims system — all with a full audit trail for state regulators."

46. "Our reinsurance brokerage manages treaty placements for 200 cedents. Each treaty has complex layering structures with multiple reinsurers. We need a consolidated exposure analytics platform that can aggregate natural catastrophe exposure across all treaties, run PML calculations against RMS and AIR models, and produce bordereaux reports for Lloyd's. The data currently lives in spreadsheets managed by 30 different brokers."

## Agriculture & Food Supply

47. "We're a precision agriculture company with 50,000 connected soil sensors deployed across farms in the Midwest. Sensors report moisture, pH, nitrogen, and potassium levels every 15 minutes. We combine this with satellite imagery from Planet Labs (updated weekly), USDA crop progress reports, and 10-day weather forecasts from DTN. Our agronomists need field-level recommendations for fertilizer application, but farmers want a simple mobile dashboard showing just their fields."

48. "Our grain trading operation handles 2 million metric tons annually across 40 elevators. We need to track basis prices at each elevator in real-time against CBOT futures, monitor rail car availability from BNSF and UP, and optimize logistics to minimize transportation costs. The margin on each bushel is $0.03 so every hour of delay matters. Currently our traders use 12 different spreadsheets updated manually."

49. "We're a food safety company providing traceability solutions for the fresh produce supply chain. When the FDA issues a recall, we need to trace contaminated product from retail shelf back to the specific farm, harvest date, and lot number within 2 hours — that's the FDA's FSMA 204 requirement. Our data comes from 500 growers, 30 processing facilities, and 15 distribution centers, each with different ERP systems."

## Construction & Infrastructure

50. "We're a commercial construction company managing 25 active job sites. Each site has IoT-connected concrete sensors (maturity monitoring), crane load cells, and environmental monitors. Project managers need real-time safety dashboards, but our estimating team needs historical productivity data to improve bid accuracy on future projects. We're currently spending $40K/month on Procore and Autodesk BIM 360 but getting no cross-project analytics."

51. "Our DOT manages 12,000 miles of state highways. We have 3,000 traffic sensors, 800 weather stations, and 200 CCTV cameras feeding data 24/7. We need real-time traffic flow optimization and incident detection, but also quarterly pavement condition reports for the federal Highway Performance Monitoring System. The CCTV feeds generate 50TB of video per day and we only keep it for 30 days."

52. "We're a structural engineering firm doing bridge inspections for 3 state DOTs. Each inspection generates a 200-page report with photos, LiDAR scans, and NDE test results. We have 15 years of inspection data across 4,000 bridges and want to build deterioration prediction models to prioritize maintenance spending. The engineers use AutoCAD and don't want to learn new tools."

## Maritime & Shipping

53. "Our container shipping line operates 45 vessels across 12 trade lanes. Each vessel has 2,000 sensors monitoring engine performance, fuel consumption, hull stress, and weather conditions — transmitting via Inmarsat satellite every 30 minutes. We need predictive maintenance for main engines (each overhaul costs $2M), voyage optimization for fuel savings, and emissions reporting for the IMO's Carbon Intensity Indicator requirements."

54. "We run a port terminal handling 3 million TEUs per year. Yard tractors, gantry cranes, and reach stackers all send telemetry data. We need to optimize container stacking and retrieval sequences to reduce vessel turnaround time. Currently a 10,000 TEU vessel takes 36 hours to work — our KPI target is 28 hours. We also need to track dwell times for customs compliance and generate SOLAS VGM certificates for every outbound container."

## Mining & Natural Resources

55. "We operate 3 open-pit copper mines in Chile and Peru. Each mine has 200 haul trucks, 15 shovels, and 8 drill rigs — all equipped with Modular Mining dispatch systems. We need real-time fleet management dashboards showing cycle times, payload optimization, and fuel burn. Our geologists also need to correlate drill blast-hole assay data with the block model to improve grade control. The mines are at 4,000m altitude with unreliable cellular coverage."

56. "Our timber company manages 500,000 acres of managed forest. We use LiDAR surveys every 3 years, satellite change detection monthly, and ground-based inventory plots annually. We need to build a timber volume forecasting model that combines all three data sources with growth-and-yield projections. The forestry team uses R and wants to keep using it. We also need to generate Forest Stewardship Council audit reports annually."

## Gaming & Entertainment

57. "We're a mid-size mobile gaming studio with 8 million DAU across 3 titles. Our games generate 2 billion events per day — session starts, level completions, IAP transactions, ad impressions. We need real-time A/B test monitoring (we run 20 concurrent experiments), daily LTV cohort analysis, and monthly financial reporting for our publisher. Our analytics team is 4 people using Amplitude and BigQuery, but we're hitting BigQuery's $50K/month spend limit."

58. "Our casino operates 3,000 slot machines and 200 table games. Each slot machine reports every spin, win, and bonus trigger. We need real-time floor optimization — moving hot machines to high-traffic areas, detecting advantage players, and monitoring for Title 31 CTR compliance. The gaming commission requires us to retain all transaction data for 7 years with tamper-proof audit trails. We're currently on an AS/400 system from 1998."

## Public Safety & Emergency Services

59. "We're a county 911 dispatch center handling 500,000 calls per year. We need to analyze response time patterns, predict call volumes by hour and day of week for staffing optimization, and generate NENA i3 compliance reports. Our CAD system exports XML data nightly but the format changes with every vendor update. We also want to correlate 911 data with hospital ED admission times to measure the full emergency response chain."

60. "Our state emergency management agency needs a common operating picture during natural disasters. We ingest data from NWS weather alerts, USGS earthquake sensors, FEMA damage assessments, social media sentiment (Twitter/X firehose), and field reports from 67 county EMAs. During Hurricane season, data volume spikes 100x and the platform must stay responsive. Between events, the same platform is used for training exercise after-action reports."

## Biotech & Life Sciences

61. "Our biotech company runs clinical trials across 45 sites in 12 countries. Each site submits electronic case report forms through Medidata Rave, adverse event reports through our safety database, and lab results from 8 different central labs. We need a unified trial analytics dashboard that shows enrollment velocity, protocol deviations, and safety signals in near-real-time. The FDA expects us to produce ISS/ISE datasets in CDISC SDTM format within 60 days of database lock."

62. "We're a genomics startup processing whole-genome sequencing data. Each sequencing run produces 150GB of FASTQ files that need to be aligned, variant-called, and annotated. We process 200 samples per week. Our bioinformaticians use Nextflow pipelines on AWS Batch, but our clinical geneticists need a simple web interface to query variants against ClinVar, gnomAD, and our internal database of 50,000 previously processed genomes."

63. "Our contract research organization runs bioequivalence studies for generic drug manufacturers. We generate pharmacokinetic datasets (Cmax, AUC, Tmax) from plasma sample analysis on LC-MS/MS instruments. We need automated PK parameter calculation, statistical analysis (ANOVA for crossover designs), and FDA submission-ready tables/listings/figures. Currently our biostatisticians spend 3 weeks per study on SAS programming that could be templated."

## Fintech & Payments

64. "We're a neobank with 2 million customers. Our core banking system processes 15 million transactions per day. We need real-time fraud scoring (sub-100ms per transaction), AML transaction monitoring with SAR filing automation, and customer 360 profiles that combine transaction patterns, app engagement, and customer support interactions. We're on AWS today but the board wants to evaluate Azure for our European expansion due to GDPR data residency requirements."

65. "Our payment processing platform handles $2B in annual volume for 50,000 merchants. We need to detect payment anomalies in real-time — declined transaction spikes, unusual refund patterns, and potential merchant fraud. Merchants also want self-service analytics dashboards showing settlement reports, chargeback rates, and customer demographics. We process through Visa, Mastercard, and ACH and each network has different reconciliation file formats."

## Hospitality & Travel

66. "We manage 150 hotels across 3 brands. Our PMS (Opera) tracks 2 million room-nights per year. Revenue managers need real-time rate optimization based on demand signals — competitor pricing from OTAs, local event calendars, flight search volume, and historical booking patterns. Currently each hotel's RM adjusts rates manually using spreadsheets. We also need to consolidate guest profiles across brands for our loyalty program — same guest might be in 3 different PMS instances."

67. "Our airline operates 400 daily flights with a fleet of 80 aircraft. We need to optimize crew scheduling, predict maintenance needs from aircraft sensor data (engine EGT trends, APU performance), and provide real-time irregular operations management when weather disrupts the network. Our ops control center currently uses 6 different legacy systems that don't talk to each other. DOT on-time performance reporting is also required monthly."

## Renewable Energy & Sustainability

68. "We operate 12 wind farms with 500 turbines total. Each turbine's SCADA system generates 200 data points every second — wind speed, blade pitch, generator temperature, vibration spectra. We need predictive maintenance to reduce unplanned downtime (currently 8% vs. industry target of 3%), wind power forecasting for grid dispatch obligations, and monthly ESG reporting for our investors. Our sites are remote with satellite-only connectivity at 4 of the 12 farms."

69. "Our utility company is deploying 500,000 smart meters over the next 2 years. Meters report 15-minute interval consumption data via RF mesh network. We need a meter data management system that handles 48 million readings per day, calculates time-of-use billing, detects electricity theft through consumption pattern anomalies, and provides customers with real-time usage dashboards. Our existing MDM is a 15-year-old Oracle system that can't handle the volume."

## Automotive & Manufacturing

70. "We're a Tier 1 automotive supplier producing brake components for 6 OEMs. Each production line has 50 inspection stations with machine vision cameras capturing part images at 30fps. We need real-time defect detection using computer vision models, SPC chart monitoring for process drift, and traceability linking each part to its specific material batch, machine settings, and inspection images. IATF 16949 requires us to retain quality records for 15 years plus 1 year."

71. "Our EV battery manufacturing plant produces 5,000 cells per day. Each cell goes through 47 process steps with 200+ parameters recorded per step — electrode coating thickness, electrolyte fill volume, formation cycling profiles. We need to correlate manufacturing parameters with cell performance data from our 6-month aging study to optimize yield. Currently our process engineers query a historian database with 2 billion rows using ad-hoc SQL and it takes 45 minutes per query."

## Government & Civic Tech

72. "Our city's transportation department needs to integrate data from 15,000 parking meters, 200 traffic signals with adaptive control, 50 bike-share stations, and 3 transit agencies. We want to build a mobility dashboard for city council showing congestion patterns, transit ridership trends, and parking utilization. We also need to publish open data feeds in GTFS and GBFS formats for third-party app developers. The data is currently siloed across 8 different vendor platforms."

73. "We're a state tax authority processing 8 million individual and 500,000 business tax returns annually. We need to build fraud detection models to identify suspicious returns before refunds are issued — currently we lose $200M per year to fraudulent refunds. The model needs to score returns within 24 hours of filing, flag high-risk returns for auditor review, and maintain a full decision audit trail for legal proceedings. All data must stay within our state-operated data center per state law."

## Legal & Compliance

74. "Our AmLaw 100 law firm handles 500 matters per year, each generating 50GB-5TB of documents for e-discovery. We need a document review platform that uses NLP to classify documents by privilege, relevance, and responsiveness. TAR (Technology Assisted Review) models need to achieve 80%+ recall while reducing human review costs by 60%. We must maintain defensible chain of custody and produce EDRM XML load files for opposing counsel."

75. "We're the compliance department of a global bank with operations in 40 countries. We need to monitor all employee communications — emails, Bloomberg chats, Teams messages, WhatsApp — for potential market abuse, insider trading, and conflicts of interest. That's 50 million messages per day. Regulators in the US (SEC), UK (FCA), and Hong Kong (SFC) each have different retention and surveillance requirements. Our current Relativity deployment can't keep up with the volume."

## Logistics & Supply Chain

76. "Our 3PL company manages warehouse operations across 25 fulfillment centers. We handle 500,000 orders per day during peak season (Black Friday through Christmas) with SKU counts exceeding 2 million unique items. We need real-time inventory visibility across all locations, predictive demand planning to pre-position inventory, and automated carrier selection based on cost, transit time, and delivery performance. Our WMS is Manhattan Associates and our TMS is BluJay — neither shares data well with the other."

77. "We're a cold chain logistics provider transporting pharmaceuticals and biologics. Every shipment has IoT temperature loggers recording at 1-minute intervals. We need real-time excursion alerts (if temperature goes outside 2-8°C range), predictive analytics for which shipping lanes have the highest excursion risk, and automated GDP compliance documentation for each shipment. One temperature excursion on a biologic can destroy $500K worth of product."

## PropTech & Real Estate

78. "Our REIT manages 80 Class A office buildings totaling 30 million square feet. Each building has a BMS (Siemens or Johnson Controls) monitoring 10,000+ HVAC data points. Occupancy sensors track floor utilization in real-time. We need energy benchmarking against ENERGY STAR, predictive maintenance for chillers and air handlers, and tenant comfort scoring. We also need to model the ROI of LED retrofit projects across the portfolio. Our building engineers are not data people — they need simple dashboards."

79. "We're a residential real estate marketplace processing 2 million listings per year. We want to build an automated valuation model (AVM) using MLS data, county assessor records, satellite imagery (for roof condition and lot characteristics), and neighborhood amenity data from OpenStreetMap. The model needs to predict sale prices within 5% accuracy for 80% of properties. Real estate agents want API access to embed valuations in their CRM, and consumers want a public-facing search tool."

## EdTech & Higher Education

80. "Our university's institutional research office needs to build a student success analytics platform. We have data in Banner (SIS), Canvas (LMS), Slate (admissions CRM), and TouchNet (financial). We want to predict first-year retention risk using pre-enrollment characteristics and early-semester engagement signals from Canvas — assignment submissions, LMS login frequency, discussion board participation. FERPA compliance is non-negotiable and our IR team of 4 only knows Tableau and Excel."

81. "We're an online learning platform with 5 million registered learners. Our courses generate clickstream data — video plays, pauses, seeks, quiz attempts, forum posts — averaging 500 million events per day. We need real-time adaptive learning paths that adjust content difficulty based on learner performance, weekly engagement cohort analysis for our content team, and monthly completion rate reports for our B2B enterprise clients. Our current Snowflake setup costs $30K/month and leadership wants to evaluate alternatives."

## Cybersecurity & InfoSec

82. "Our MSSP monitors security events for 200 client organizations. We ingest 50 billion log events per day from firewalls, endpoint agents, cloud audit logs, and identity providers. Our SOC analysts need sub-5-second search across 90 days of data, automated alert correlation and triage, and MITRE ATT&CK mapping for threat hunting. We're currently on Splunk Enterprise at $1.2M/year and the board wants us to find a more cost-effective solution that can still handle the volume."

83. "We're building an insider threat detection program for a defense contractor. We need to analyze badge access logs, VPN connections, file access patterns, email metadata (not content), and USB device usage across 15,000 employees. The system needs to establish behavioral baselines per user and flag anomalies — like an engineer accessing classified documents at 3am from a foreign IP. All analytics must run in our air-gapped SCIF network with no cloud connectivity."

## Water & Waste Management

84. "Our water utility serves 2 million customers across 3 counties. We have 500 SCADA-connected pump stations, 50 water treatment facilities, and 8,000 miles of distribution pipes. We need real-time pressure and flow monitoring to detect leaks and main breaks, demand forecasting for reservoir management, and EPA compliance reporting for Safe Drinking Water Act parameters. Our SCADA data is on OPC-DA protocol and our billing system is a 20-year-old COBOL application."

85. "We're a waste management company operating 15 landfills and 8 MRFs (material recovery facilities). Each MRF has optical sorting machines that classify 200 tons of recyclables per day using computer vision. We need to optimize sort line efficiency, track contamination rates by collection route, and generate monthly diversion reports for municipal contracts. We also monitor landfill gas wells for methane levels — exceedances require immediate EPA notification within 1 hour."

## Sports & Athlete Performance

86. "Our professional soccer league tracks player movement using GPS vests during training and optical tracking (Hawk-Eye) during matches. Each match generates 25 million data points — player positions at 25fps, ball position, sprint distances, acceleration profiles. Coaching staff want post-match performance reports within 30 minutes of the final whistle. Sports scientists want to correlate training load with injury incidence over the season. Broadcast partners want real-time statistics for on-screen graphics."

87. "We're building a sports betting analytics platform. We ingest odds feeds from 20 bookmakers updating every second, historical match results from 50 leagues worldwide, and real-time match event data (goals, cards, substitutions). We need to calculate implied probabilities, detect line movement anomalies that suggest sharp action, and provide our trading desk with real-time exposure monitoring across 10,000 concurrent markets. Our current system processes 500,000 odds updates per second during peak Premier League weekends."

## Fashion & Retail Analytics

88. "Our fashion brand has 300 stores globally and an e-commerce platform doing $500M in annual revenue. We need to optimize inventory allocation across channels — sizing and color assortments vary by region. We want to use sell-through velocity data combined with social media trend signals (Instagram, TikTok mentions) to predict which styles will be bestsellers 6 weeks before the season starts. The merchandising team currently makes allocation decisions using last year's sales data in Excel pivot tables."

89. "We run a luxury resale marketplace authenticating and selling 50,000 items per month. Each item is photographed from 8 angles, measured, and assessed for condition by our authentication team. We want to build a pricing model that considers brand, condition, age, current retail price, and market demand. We also need computer vision models to assist with authentication — detecting counterfeit stitching patterns, hardware engravings, and material textures. Our catalog has 2 million items with 16 million images."

## Space & Satellite

90. "We operate a constellation of 150 Earth observation satellites. Each satellite generates 200GB of multispectral imagery per orbit (14 orbits per day). Ground stations download data during 10-minute pass windows. We need an automated imagery processing pipeline — radiometric correction, orthorectification, cloud masking, and change detection — that produces analysis-ready data within 6 hours of capture. Our government customers need to search and order imagery through a STAC-compliant API. Current processing backlog is 72 hours."
