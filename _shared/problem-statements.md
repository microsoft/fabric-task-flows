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
