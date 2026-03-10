# Problem Statements for Stress Testing

> Auto-generated batch 10 — 50 problems designed to stress-test edge cases: extremely short, extremely long, multi-paragraph, contradictory requirements, emerging tech buzzwords, and pure operational problems.

## Ultra-Short (1-2 Sentences)

1. "We need real-time fraud detection."

2. "Our data warehouse is too slow."

3. "We want to build a recommendation engine."

4. "We need to process IoT sensor data."

5. "Data quality is killing us."

6. "We need a data catalog."

7. "Our ETL jobs keep failing."

8. "We need to do NLP on customer feedback."

9. "We need streaming analytics."

10. "Our reports are always wrong."

## Multi-Paragraph Deep Dives

11. "We have a complex situation. Our organization runs 14 different source systems generating approximately 2TB of data per day. These range from ERP systems to custom-built applications to third-party SaaS platforms. Currently, each department has built its own data pipeline independently, resulting in 47 separate ETL processes that nobody fully understands. Some run on scheduled CRON jobs, others are triggered by file drops, and a few are manually initiated by analysts who run Python scripts on their laptops. The data eventually lands in three different data warehouses, two data lakes, and countless shared drives. We've tried to standardize three times in the past five years and failed each time because we couldn't get organizational buy-in. Now our new CTO is mandating a unified approach and we have 18 months to deliver. We also need to maintain backward compatibility with all existing downstream consumers — there are over 200 reports and dashboards that people rely on daily."

12. "Our predictive maintenance program has been a partial success but we're hitting limitations. We currently monitor vibration, temperature, and pressure sensors on 3,000 pieces of equipment across 12 facilities. Our existing system uses simple threshold-based alerting — when a reading exceeds a predefined limit, we generate an alert. The problem is twofold: first, we get too many false positives because thresholds don't account for normal operational variations. Second, we miss gradual degradation patterns that don't trigger any single threshold but indicate impending failure when viewed holistically. We need to move from threshold-based to pattern-based anomaly detection. We also want to incorporate maintenance logs, spare parts inventory, production schedules, and weather data into our predictions. Our data science team has built promising models in R and Python but they only work with historical data — we need these running in near-real-time against streaming sensor data."

13. "We're a mid-size company that recently acquired two competitors. Between the three organizations, we have approximately 4 million customer records with significant overlap. Customer John Smith might appear as J. Smith in one system, John A. Smith in another, and SMITH, JOHN in the third — with different email addresses, phone numbers, and mailing addresses across all three. We need to create a single, authoritative customer record for each unique person while preserving the history from all three source systems. We also need to establish ongoing governance so that as new customer data comes in, it's automatically matched and merged. The regulatory implications are significant — several customers have opted out of data sharing under privacy regulations, and those preferences must be honored during the merge. We estimate this will affect 200+ downstream applications and reports."

14. "Our data science team spends 80% of their time on data preparation and only 20% on actual modeling. They need access to production data but getting it requires going through a 6-week security review process. Once they get the data, it's often stale or incomplete. They build models in Jupyter notebooks that work great locally but take months to deploy to production because our ML engineering team has to rewrite everything. We've tried MLflow and Kubeflow but neither integrated well with our existing infrastructure. We need an end-to-end ML platform that handles data access, feature engineering, model training, deployment, monitoring, and retraining — without requiring our data scientists to become DevOps engineers."

15. "Our customer-facing application serves 50 million monthly active users globally. Response times need to be under 200ms at the 99th percentile. We currently cache aggressively but our cache invalidation logic is broken — users sometimes see stale data for hours. We need a system that can serve personalized content recommendations, real-time pricing, and inventory availability checks while maintaining sub-200ms response times. The backend data changes constantly — prices update every 15 minutes, inventory changes with every transaction, and new content is published hourly. We also need the ability to A/B test different algorithms without affecting performance."

## Contradictions and Trade-offs

16. "We need our data to be both completely open for innovation and locked down for compliance. Everyone should be able to experiment but nothing should ever break production."

17. "We want real-time analytics but our budget only allows for batch processing."

18. "We need perfect data quality but we can't slow down our ingestion pipeline."

19. "We want a completely automated data platform but we also need human approval for every change."

20. "We need to process petabytes of historical data and also handle real-time streams, but we only have a team of three."

## Emerging Technology Buzzwords

21. "We want to implement a data mesh with federated governance."

22. "We need a lakehouse architecture with ACID transactions."

23. "We want to build a knowledge graph from our enterprise data."

24. "We need vector search capabilities for our RAG pipeline."

25. "We want to implement data contracts between our producer and consumer teams."

26. "We need a feature platform for our ML models with point-in-time correctness."

27. "We want to build a real-time data product catalog."

28. "We need change data capture from our legacy databases."

29. "We want to implement a medallion architecture with Delta Lake."

30. "We need reverse ETL to push analytics back into our operational systems."

## Pure Operational Problems

31. "Our overnight batch jobs used to finish by 6 AM but now they're running until noon. Nothing changed in the code — the data volume just keeps growing."

32. "We deploy changes to our data pipeline on Fridays and something always breaks over the weekend."

33. "We have no idea which reports are actually being used. We're afraid to retire anything because someone might need it."

34. "Our data lake has become a data swamp. There are 50,000 files and nobody knows what most of them contain."

35. "When our primary database goes down, we lose everything. We have no disaster recovery plan for our analytics infrastructure."

36. "Our Spark jobs keep running out of memory and we don't know why."

37. "We're paying $200K per month for cloud data services and leadership wants us to cut it to $100K without losing functionality."

38. "Our data lineage is nonexistent. When a number looks wrong in a report, it takes days to trace back to the source."

39. "We process credit card transactions and our current system can't handle Black Friday volumes. Last year we had to queue transactions for 4 hours."

40. "Our team manages 300 Apache Airflow DAGs and when one fails at 2 AM, it cascades into 40 other failures."

## Mixed-Signal Complex Scenarios

41. "We have sensor data from 10,000 devices updating every second. We need to detect anomalies in real-time, store the raw data for compliance, train ML models on historical patterns, and serve aggregated metrics through an API — all while keeping costs under $50K per month."

42. "Our company is going through a digital transformation. We need to migrate from on-premises SQL Server to the cloud, implement a self-service analytics platform, add predictive capabilities, and establish proper data governance — but our IT team is already stretched thin maintaining the existing systems."

43. "We're building a customer 360 view that requires combining transactional data, behavioral data from our website, support ticket history, social media sentiment, and third-party demographic data. The transactional data updates in real-time, behavioral data is sessionized hourly, support tickets come in as events, social media is batched daily, and demographics are refreshed quarterly."

44. "Our regulatory reporting takes a team of 12 people three weeks every quarter. They manually pull data from eight systems, reconcile discrepancies, apply business rules, generate reports in specific formats, and submit them through a government portal. We want to automate as much as possible while maintaining auditability."

45. "We're a startup with a data-intensive product. We need to ingest data from customer APIs in various formats (JSON, XML, CSV, Parquet), normalize it, apply business logic, store results, and expose them through our own API — all with multi-tenant isolation so Customer A never sees Customer B's data."

46. "Our marketing team wants to run experiments at scale. They need to segment customers based on behavior, set up control and test groups, deploy personalized content, measure results in real-time, and automatically roll out winning variations — but they don't know SQL or Python."

47. "We have a fleet of autonomous vehicles generating 4TB of data per vehicle per day. We need to stream critical telemetry for safety monitoring, batch-process the full dataset for model training, and maintain a queryable archive for incident investigation. Latency for safety alerts must be under 100ms."

48. "Our supply chain spans 200 suppliers across 30 countries. We need to track shipments in real-time, predict delays based on weather and geopolitical events, optimize routing, and provide customers with accurate delivery estimates. The data comes from EDI messages, GPS trackers, weather APIs, news feeds, and customs databases."

49. "We're building a clinical research platform. Patient data must be de-identified for research while maintaining referential integrity. Researchers need to query across studies without seeing individual patient records. All access must be logged, all changes must be auditable, and the platform must comply with HIPAA and GDPR simultaneously."

50. "Our e-commerce platform needs to serve product recommendations in under 50ms, retrain models every hour with the latest behavioral data, detect fraudulent transactions in real-time, generate nightly business reports for category managers, and handle 10x traffic spikes during sales events — all on a startup budget."
