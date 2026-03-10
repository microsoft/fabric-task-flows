# Problem Statements for Stress Testing

> Auto-generated batch 1 — 50 problems at varying depth (vague, semi-detailed, detailed) for self-healing loop.

## Cloud Migration & Modernization

1. "We need to move our data to the cloud."

2. "Our company has 50 on-prem SQL Server databases ranging from 10GB to 2TB that we need to migrate to a modern cloud analytics platform. We want to consolidate them into a single source of truth with proper data governance. Teams currently run ad-hoc queries directly against production and we need to stop that."

3. "We're lifting and shifting our legacy data warehouse but also want to modernize our reporting. Right now everything runs on nightly stored procedures."

## Predictive Maintenance & Equipment Monitoring

4. "Our machines break down and we want to predict when they'll fail."

5. "We run a fleet of 500 industrial compressors across 12 manufacturing sites. Each unit has vibration sensors sampling at 10kHz, temperature probes reading every second, and oil analysis data collected monthly. We need to detect bearing degradation 2-3 weeks before failure, schedule maintenance during planned downtime windows, and track mean time between failures per compressor model. Our reliability engineers use MATLAB but are willing to learn Python."

6. "We have 200 CNC machines and want to monitor spindle health. The machines generate alarm logs, cycle time data, and power consumption readings. We want to know which machines are degrading before they cause scrap parts."

## Customer Analytics & Personalization

7. "We want to understand our customers better and personalize their experience."

8. "Our e-commerce platform processes 2 million orders per month from 8 million registered users. We track clickstream data, purchase history, returns, customer service interactions, and email engagement. We want to build customer lifetime value models, churn prediction, and real-time product recommendations. Our marketing team needs self-service dashboards they can slice by cohort, channel, and geography."

9. "We have a loyalty program with 5 million members. We want to segment them and predict who's about to leave."

## Financial Reporting & Compliance

10. "We need better financial reports."

11. "Our multinational corporation operates in 35 countries with different accounting standards (IFRS, US GAAP, local GAAP). We consolidate financials from 200 legal entities monthly through a painful manual process in Excel. We need automated intercompany elimination, currency translation, and regulatory report generation. SOX compliance requires full audit trails for every adjustment. Our finance team has zero technical skills."

12. "We're a publicly traded company that needs to automate our SEC 10-K and 10-Q filing data extraction. Currently our IR team manually copies numbers from the ERP into filing templates. We need reconciliation checks and version control for every submission."

## Supply Chain Optimization

13. "Help us optimize our supply chain."

14. "We're a global consumer goods company with 15 factories, 50 distribution centers, and 200,000 retail points of sale. We need demand forecasting at the SKU-location-week level, inventory optimization across the network, and supplier lead time prediction. Our planners currently use spreadsheets and gut feel. We have 3 years of POS data, weather data, and promotional calendars. Stockouts cost us $50M annually."

15. "Our warehouse ships 10,000 orders daily and we want to optimize picking routes and predict staffing needs based on order volume patterns."

## Healthcare Data Integration

16. "We need to bring all our patient data together."

17. "Our hospital network spans 8 facilities generating HL7 FHIR messages, DICOM imaging studies, lab results in various formats, and unstructured clinical notes. We need a longitudinal patient record for population health analytics, readmission risk scoring, and clinical trial recruitment. HIPAA compliance is non-negotiable. Our clinical informatics team is 3 people."

18. "We're a health plan processing 10 million claims per year. We need to detect fraudulent billing patterns, identify high-risk members for care management programs, and produce HEDIS quality measure reports for NCQA accreditation."

## Energy & Utility Management

19. "We want to be smarter about our energy usage."

20. "Our electric utility serves 2 million customers with smart meters reporting consumption every 15 minutes. We need load forecasting for grid operations, outage detection from meter-last-gasp signals, theft detection from consumption anomalies, and customer-facing usage dashboards. Our SCADA system feeds real-time grid sensor data at 4-second intervals. We must comply with NERC CIP cybersecurity requirements."

21. "We manage 500 commercial buildings and want to benchmark energy performance, detect HVAC inefficiencies, and generate monthly sustainability reports for our ESG commitments."

## Logistics & Fleet Management

22. "We need to track our trucks."

23. "Our delivery company operates 2,000 vehicles making 50,000 deliveries per day across 15 metro areas. Each truck has GPS updating every 10 seconds, temperature sensors for cold chain compliance, and driver behavior telemetry. We need real-time route optimization, ETA prediction with 15-minute accuracy, proof-of-delivery capture, and DOT hours-of-service compliance tracking. Dispatchers need a live map."

24. "We run a last-mile delivery operation and want to predict delivery windows more accurately. Customers currently get 4-hour windows and complain."

## Quality Control & Defect Detection

25. "Our products have too many defects and we need to figure out why."

26. "Our electronics assembly line produces 50,000 circuit boards per day across 6 SMT lines. We do automated optical inspection (AOI), X-ray inspection for BGA components, and in-circuit testing. Currently defect root cause analysis takes 2 days because engineers manually correlate defects with solder paste printer settings, reflow oven profiles, and component lot numbers. We need automated traceability from defect to root cause in minutes."

27. "We manufacture injection-molded plastic parts. Each press has 30 process parameters — temperature, pressure, cooling time — and we want to correlate parameter drift with part dimension variation measured by CMM."

## HR & Workforce Analytics

28. "We want to use data to make better people decisions."

29. "Our company has 25,000 employees across 40 offices. We collect data from our HRIS (Workday), performance reviews, engagement surveys, learning management system, and time tracking. We need attrition prediction models, skill gap analysis for workforce planning, DEI metrics reporting, and compensation benchmarking. Our HR team can use Power BI but nothing more technical. All data is PII-sensitive."

30. "We're growing fast — 500 new hires per quarter — and need to predict which candidates will accept offers and which new hires are at risk of early turnover."

## Marketing Attribution & Campaign Analytics

31. "We want to know which marketing channels actually work."

32. "Our B2B SaaS company spends $20M annually across paid search, content marketing, events, webinars, social media, and SDR outreach. We need multi-touch attribution modeling connecting marketing touchpoints to closed-won revenue in Salesforce. The average sales cycle is 9 months with 15+ touches. We want to model marketing mix optimization and predict pipeline generation by channel and spend level."

33. "We run email campaigns to 2 million subscribers and want to optimize send times, subject lines, and content based on past engagement patterns."

## Environmental Monitoring & Compliance

34. "We need to monitor our environmental impact."

35. "Our mining operation covers 50 square kilometers with 200 groundwater monitoring wells, 15 air quality stations, and 30 surface water sampling points. We collect data monthly for regulatory compliance but want continuous automated monitoring. We need to detect contamination plumes early, generate regulatory reports for the EPA, and maintain chain-of-custody records for all samples. Our environmental scientists use ArcGIS and Excel."

36. "We're a food manufacturer tracking Scope 1, 2, and 3 greenhouse gas emissions across our entire value chain. We need to consolidate data from factories, logistics partners, and raw material suppliers into an auditable carbon accounting system."

## Real Estate & Property Management

37. "We want to use data to manage our properties better."

38. "We manage 500 commercial office buildings totaling 80 million square feet. We need occupancy analytics from badge swipe data, predictive maintenance scheduling for HVAC and elevator systems based on equipment sensor data, lease expiration forecasting, and tenant satisfaction tracking. Our property managers are non-technical and need mobile-friendly dashboards showing building health scores."

39. "We're a residential REIT with 20,000 apartment units. We want to optimize rental pricing based on market comps, vacancy trends, and seasonal demand patterns."

## Fraud Detection & Risk Management

40. "We need to catch fraud faster."

41. "Our payment processor handles 50 million transactions per day across credit cards, ACH transfers, and digital wallets. We need sub-100ms fraud scoring for each transaction, behavioral biometrics analysis, merchant risk profiling, and regulatory reporting for suspicious activity (SARs). False positive rates must stay below 2% to avoid customer friction. We process transactions 24/7 with no maintenance windows."

42. "We're an insurance company and suspect some of our auto claims are staged. We want to identify suspicious claim patterns — same body shops, same attorneys, similar accident descriptions."

## Education & Learning Analytics

43. "We want to improve student outcomes with data."

44. "Our university system has 60,000 students across 5 campuses. We collect data from our LMS (Canvas), student information system, financial aid, advising records, and campus facilities usage. We want early warning models for students at risk of dropping out, course recommendation engines, and institutional effectiveness dashboards for accreditation reporting. FERPA compliance is required. Faculty governance means any changes take forever."

45. "We run an online learning platform with 100,000 active learners. We want to identify which course content leads to the best completion rates and assessment scores."

## Agriculture & Food Production

46. "We want to farm smarter."

47. "Our precision agriculture company manages 500,000 acres across 200 farms. We collect data from soil sensors, weather stations, drone imagery, yield monitors on combines, and satellite NDVI imagery. We need field-level yield prediction, variable rate application maps for fertilizer and seed, disease detection from aerial imagery, and regulatory compliance reporting for USDA subsidies. Most farmers access our platform from tablets with spotty cellular coverage."

48. "We're a food processing company tracking ingredients from farm to finished product. We need full lot traceability for recall management and FSMA compliance."

## Telecommunications & Network Operations

49. "Our network keeps having problems and we can't figure out why."

50. "Our telecom company operates 50,000 cell towers serving 10 million subscribers. Each tower generates performance metrics — signal strength, handover success rate, dropped call rate, throughput — every minute. We need anomaly detection to identify degrading towers before customers complain, capacity planning for 5G rollout, and customer experience scoring that correlates network KPIs with NPS survey results. Our NOC team needs real-time dashboards with drill-down from regional to individual tower views."
