# Problem Statements for Stress Testing

> Auto-generated batch 5 — 50 problems at varying depth (vague, semi-detailed, detailed) for self-healing loop. Final batch — emphasis on natural language idioms, unusual phrasing, and edge cases.

## Ultra-Vague Conversational (No Tech Jargon)

1. "Our CEO asked 'why are our numbers so bad?' and nobody could answer."

2. "We keep getting surprised."

3. "I just joined and I can't find anything."

4. "How do we know if we're doing a good job?"

5. "We're making decisions based on gut feel."

6. "Nobody reads the reports we produce."

7. "Our team is drowning."

8. "We can't tell what happened last quarter."

9. "The left hand doesn't know what the right hand is doing."

10. "Why does it take a week to get a simple number?"

## Implicit Tech Intent (Conversational Phrasing)

11. "People keep asking me the same questions over and over about our data. I wish they could just look it up themselves."

12. "We need to know the instant something goes sideways, not find out two days later from a customer complaint."

13. "We've got sensors on everything but all the data just sits in a folder and nobody looks at it."

14. "Every time our CEO asks a question about the business, it takes three analysts two weeks to pull the answer together."

15. "We built a bunch of models in notebooks but they never made it to production. They just sit there doing nothing."

16. "Our competitors seem to know things about the market before we do."

17. "The sales team has their own truth, the operations team has their own truth, and finance has their own truth. Who's right?"

18. "We get raw data dumps from our partners and it takes forever to make them usable."

19. "Our customers want to see their own data in a portal but we can't expose our backend systems directly."

20. "We need to connect what's happening on the shop floor to what's happening in the back office."

## Complex Multi-Signal (Realistic Enterprise)

21. "We run 50 clinics generating appointment data, electronic health records, lab results, and patient satisfaction scores. We want to predict no-shows, optimize scheduling, and produce quality metrics for our value-based care contracts. Patient data is HIPAA-protected and our clinical staff has zero analytics experience."

22. "Our logistics network has 20 warehouses with RFID-tagged inventory, GPS-tracked trucks, and customer delivery confirmations. We need real-time inventory visibility across all locations, predictive demand allocation to minimize cross-shipments, and proof-of-delivery reconciliation. The warehouse systems speak different protocols — some REST, some flat file, some message queue."

23. "We operate a network of 100 charging stations for electric vehicles. Each station reports power consumption, session duration, and error codes every minute. We want to predict equipment failures, optimize dynamic pricing based on demand patterns and grid costs, and provide drivers with real-time availability maps. The stations are in areas with unreliable cellular."

24. "Our research team publishes 200 papers per year. We have data scattered across lab notebooks, instruments, shared drives, and individual researchers' laptops. We need a research data management platform that catalogs datasets, tracks data provenance, enables replication, and satisfies our funder's data sharing requirements. Some data contains export-controlled information."

25. "We're a franchise with 500 locations. Each franchise owner runs their own POS system, and some use our recommended software while others use competing products. We need to normalize sales data across all locations into a unified view for franchise-wide performance benchmarking, but franchise owners are protective of their data and don't want corporate seeing everything."

26. "Our SaaS platform serves 5,000 B2B customers. Each customer gets a dedicated tenant in our database. We need tenant-level usage analytics for billing and capacity planning, cross-tenant anonymized benchmarking for product insights, and real-time health monitoring to detect degraded customer experiences before tickets come in."

27. "We're a utility company migrating from a 30-year-old mainframe billing system to a modern cloud platform. During the 18-month transition, both systems need to run in parallel. Customer records, rate tables, billing history, and payment data need to stay synchronized. Any billing error affects 2 million customers."

28. "Our hospital's pharmacy fills 3,000 prescriptions per day. We want to cross-reference each prescription against the patient's full medication list, lab values, and allergy records to catch dangerous drug interactions in real-time. Currently pharmacists do manual checks and they catch about 95% of interactions. We want 99.9%."

29. "We manage 10,000 rental properties. Tenants submit maintenance requests through an app, which dispatches technicians. We want to predict which properties will have maintenance issues based on age, inspection history, and weather, and proactively schedule repairs. We also need financial reporting on maintenance spend by property, region, and building type."

30. "We're a food distributor handling 100,000 orders per day with strict cold chain requirements. Temperature loggers in every truck record every 30 seconds. If a shipment's temperature goes out of range, we need to know immediately — not when the driver delivers and the customer rejects. We also need batch lot traceability for FSMA recall compliance."

## Edge Cases — Ambiguous or Conflicting Signals

31. "We have real-time data but we only need weekly reports. The data comes in constantly but stakeholders only care about Friday summaries."

32. "We want AI but we don't have any data scientists on staff. We just want the system to figure things out automatically."

33. "Our data doesn't need to be real-time but it can't be more than 5 minutes old."

34. "We need compliance reporting but we don't know which regulations actually apply to us."

35. "We want to analyze data but we can't move it out of the country where it's generated."

36. "We want a chatbot that answers questions about our data but we don't want to use any cloud AI services for privacy reasons."

37. "Our data is mostly structured database tables but the important insights come from the text notes and comments that people attach."

38. "We don't need analytics — we need our operational systems to be smarter. When inventory drops below threshold, automatically reorder. When a machine parameter drifts, automatically adjust."

39. "We want to combine public data (weather, census, economic indicators) with our private operational data for richer analysis."

40. "We're fine with our current dashboards — we just need the data behind them to be more reliable and consistent."

## Meta/Process Problems

41. "Our data team built a great pipeline but when they left, nobody understood how it works. Now it breaks every other week and nobody can fix it."

42. "We tried a data lake two years ago and it became a data swamp. Nobody could find anything and the project was abandoned. Now we want to try again but do it right."

43. "We have five different BI tools across the organization. Some teams use Power BI, others use Tableau, some use Looker. We want to standardize but each team insists their tool is best."

44. "Our biggest problem isn't technology — it's that business stakeholders don't know what questions to ask. They say 'give us analytics' but can't define what they want."

45. "We keep starting data projects but never finishing them. We have 20 half-built pipelines, 50 abandoned dashboards, and no documentation."

## Stress Test — Extremely Long and Complex

46. "We're a multinational insurance company with operations in 25 countries. Our underwriting team needs real-time risk scoring that incorporates third-party data feeds — weather events, credit scores, property valuations, social media sentiment, and IoT sensor data from connected homes. Claims processing needs automated document extraction from police reports, medical records, and repair estimates in multiple languages. Actuarial models need historical claims data going back 20 years, normalized across different policy structures and currencies. Our reinsurance partners require standardized data feeds in ACORD format. The CFO wants a single dashboard showing combined ratio, loss development triangles, and reserve adequacy across all lines of business, updated daily. We're regulated by insurance commissioners in each state and Solvency II in the EU. Customer-facing mobile apps need to show policy details, file claims with photo uploads, and track claim status in real-time. We have 200 data engineers and they spend 70% of their time maintaining legacy ETL jobs instead of building new capabilities."

47. "We run a precision agriculture operation across 200,000 acres. We have soil moisture sensors every 50 meters reporting every 10 minutes, drone imagery captured weekly at 2cm resolution, weather stations every 5 miles, combine yield monitors logging every second during harvest, and satellite NDVI imagery every 5 days. Our agronomists want variable rate application maps for seed, fertilizer, and pesticide — field-by-field, zone-by-zone — updated daily during the growing season. After harvest, they want yield prediction models that incorporate soil type, weather, management decisions, and genetic potential. Regulators require nitrogen application records for water quality compliance. Farmers access everything from tablets with spotty cellular coverage, so the app needs to work offline and sync when connected."

48. "We operate a global supply chain with 50 factories, 200 suppliers, 100 distribution centers, and 500,000 retail points of sale across 40 countries. Each node generates transactional data in local systems with local currencies, languages, and regulatory requirements. We need real-time visibility into inventory positions across the entire network, predictive demand sensing that incorporates POS data, weather, social trends, and economic indicators, and automated supplier scorecards. Our planning team needs scenario simulation capabilities — what happens if a port closes, a supplier goes bankrupt, or demand spikes 300%. We also need sustainability tracking for Scope 1, 2, and 3 emissions across the entire chain, plus compliance with EU Deforestation Regulation requiring commodity-level traceability."

49. "We're a healthcare network with 15 hospitals, 200 clinics, and 5 million patient lives. Our clinical data comes from 8 different EHR systems (3 Epic instances, 2 Cerner, 1 Allscripts, 1 Meditech, 1 homegrown). Lab data comes from 20 reference labs in different formats. Imaging data is 10TB per month. We need a unified clinical data repository for population health analytics, real-time ADT (admit-discharge-transfer) event processing for bed management and care coordination, predictive models for sepsis, readmission, and deterioration, and patient-facing portals showing their consolidated health records. Everything must be HIPAA compliant with de-identification for research use cases. Our clinical informatics team has 5 people supporting 50,000 clinicians."

50. "We're building an autonomous vehicle testing platform. Each test vehicle generates 5TB of data per day — LiDAR point clouds at 300,000 points per second, camera feeds from 8 cameras at 30fps each, radar returns, GPS/IMU data at 100Hz, CAN bus messages from vehicle systems, and V2X communications. After each test run, engineers need to replay scenarios frame-by-frame, query events (near-misses, disengagements, edge cases), train perception models on labeled data, and compare performance across software versions. The raw data retention policy is 7 years for regulatory purposes. Data must be stored in our own data centers — no cloud. We run 50 test vehicles simultaneously."
