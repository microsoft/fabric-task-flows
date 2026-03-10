# Problem Statements for Stress Testing

> Auto-generated batch 6 — 50 problems targeting data democratization, cross-functional coordination, edge computing, and hybrid cloud scenarios.

## Vague — Business Pain (No Tech Language)

1. "Everyone asks IT for data and IT is the bottleneck."

2. "We have a hundred dashboards and none of them agree."

3. "Our monthly close takes three weeks."

4. "We keep getting blindsided by problems we should have seen coming."

5. "Different regions report metrics differently and we can't compare them."

6. "We don't even know what data we have."

7. "Our new hires take six months to become productive because they can't find anything."

8. "We announced a data strategy last year and nothing happened."

9. "Half our analysts spend their days emailing spreadsheets back and forth."

10. "The board keeps asking questions we can't answer."

## Semi-Detailed — Implicit Architecture Needs

11. "Our customer support team looks at a different screen for billing, another for order history, another for shipping status, and another for past tickets. They want one screen that shows everything about a customer in one place."

12. "We measure Net Promoter Score quarterly via surveys but by the time results come in, the issues have already escalated. We want to sense customer dissatisfaction in real-time from behavioral signals — reduced app usage, increased support contacts, declined auto-renewals."

13. "Our factories in Asia produce data overnight our time. By the time our US analysts start working, the data is 12 hours old. Some decisions can wait, but quality excursions need to be caught immediately regardless of time zone."

14. "We've built 30 machine learning models over the past two years but we have no idea which ones are still accurate. Nobody monitors them after deployment."

15. "We have strict data residency requirements — European customer data must stay in EU data centers, but our analytics team is in the US and needs to run reports across all regions."

16. "Our partners send us data in every format imaginable — EDI, flat files, APIs, even screenshots. We spend more time parsing partner data than analyzing it."

17. "We run promotions every week and need to know within an hour if a promotion is cannibalizing other products or actually driving incremental revenue."

18. "Our legal team reviews thousands of documents for litigation holds. They need to search across emails, contracts, project files, and chat messages — but these are in five different systems."

19. "We acquired a company that uses a completely different tech stack. Their data models are incompatible with ours and their team is resistant to change."

20. "Our sales forecasting is terrible. Reps enter whatever they feel like into the CRM and management layers on optimistic adjustments. We need data-driven forecasts that don't rely on human guesswork."

## Detailed — Complex Multi-System

21. "Our retail chain has 1,200 stores with POS terminals generating 5 million transactions per day. Corporate needs real-time sales dashboards showing revenue by region, category, and store, but store managers need local performance dashboards with their specific KPIs. Regional managers want to drill from region down to individual store. The challenge is that 200 stores still run our legacy POS system with batch file uploads while the other 1,000 are on the modern cloud POS with real-time event streams."

22. "We run a clinical research network spanning 50 academic medical centers. Each center has its own EHR system (Epic, Cerner, or Meditech). Researchers need to query patient populations across all centers for clinical trial eligibility screening without exposing PHI. We need a federated query model where queries go to the data rather than data coming to us. Results must be de-identified and aggregated before any data leaves the source institution."

23. "Our smart city initiative involves integrating data from traffic cameras, parking meters, public transit GPS, air quality sensors, noise monitors, and citizen complaint hotlines. We need real-time traffic signal optimization, predictive maintenance for infrastructure, and a public-facing transparency portal showing city metrics. Each data source is owned by a different city department with its own IT budget, governance rules, and political priorities."

24. "We operate a global hotel chain with 500 properties. Each property uses one of three different property management systems. We need unified guest profiles that merge data across stays, loyalty program activity, restaurant and spa spending, and customer service interactions. A guest checking in at any property should have their preferences (room temperature, pillow type, minibar stocking) automatically applied. We also need revenue management models for dynamic room pricing."

25. "Our insurance company processes 5 million auto claims per year. Each claim generates a growing file of photos, repair estimates, police reports, medical records, and adjuster notes over weeks or months. We need a claims lifecycle dashboard showing where every claim is in the process, automated fraud scoring using network analysis (identifying rings of related claims), and predictive models for reserve setting. Adjusters work on tablets in the field with intermittent connectivity."

26. "We're a biotech company with 10 active drug discovery programs. Each program generates high-throughput screening data, computational chemistry simulations, ADMET assay results, and in-vivo study data. Scientists need to compare compound profiles across assays and programs, identify structure-activity relationships, and share findings with partner organizations — but IP protection requires strict access controls on what each partner can see."

27. "Our airline's revenue management system needs to optimize 50,000 fare buckets across 500 routes in real-time based on booking velocity, competitive pricing, historical demand curves, and event calendars. Pricing analysts need what-if simulation capabilities. The system must respond to competitor fare changes within 15 minutes. We also need regulatory reporting for DOT consumer protection requirements."

28. "We manage a wind farm portfolio with 2,000 turbines across 30 sites. Each turbine has 200+ sensor channels sampled at 1Hz — vibration, oil temperature, blade pitch, generator output, wind speed. We need condition-based maintenance scheduling, power curve analytics comparing actual vs theoretical output, and grid compliance reporting showing we're meeting our power purchase agreement obligations. Remote sites have satellite-only connectivity with 500ms latency."

29. "Our university has 100,000 alumni with giving records, event attendance, career data from LinkedIn, and social media activity. Our advancement office wants propensity models for major gift solicitation, but they also need real-time event management — tracking RSVPs, check-ins, and engagement during fundraising galas. The provost wants research impact dashboards showing how donations fund specific research outcomes."

30. "We're a logistics company operating bonded warehouses in 5 countries. Every item entering and leaving must be tracked for customs compliance with different regulations per jurisdiction. We need real-time inventory visibility across all warehouses, automated customs documentation generation, duty optimization routing, and audit-ready compliance reports. Goods in transit between warehouses exist in regulatory limbo and need careful status tracking."

## Edge Cases — Organizational & Political

31. "Our CTO wants a data lakehouse. Our CFO wants to cut cloud spending by 30%. These goals are contradictory and nobody will make the call."

32. "We tried self-service analytics three times and it failed each time because data quality was too poor for business users to get reliable answers."

33. "Our data warehouse is 15 years old and everyone depends on it. We want to modernize but can't afford any downtime or disruption to existing reports."

34. "We generate more data than we can afford to store. We need intelligent tiering — hot data for recent analytics, warm for ad-hoc queries, cold for compliance retention."

35. "Our IOT devices generate data at the edge but our network can't handle sending everything to the cloud. We need to process and filter at the edge and only send aggregates and anomalies centrally."

36. "We need to combine structured data from our ERP with unstructured feedback from customer emails, chat logs, and voice recordings to get a complete picture."

37. "We have 50 data engineers and they all build pipelines differently. There's no standardization and no reuse. Every new project starts from scratch."

38. "Our compliance team needs to prove to regulators that our AI models are fair, explainable, and don't discriminate against protected classes."

39. "We want to monetize our data — sell anonymized, aggregated insights to third parties — but we're not sure what's legally permissible or technically feasible."

40. "Our CEO read an article about digital twins and now wants one for our entire supply chain. Nobody on our team knows what that actually means in practice."

## Stress Test — Minimal Signal Problems

41. "Help."

42. "Data."

43. "We need something."

44. "It's broken."

45. "Can you fix our stuff?"

46. "What should we do with our information?"

47. "We're behind our competitors."

48. "Things used to work but they don't anymore."

49. "Our investors are asking tough questions about our operational efficiency."

50. "We want to be a data-driven organization but we don't know where to start."
