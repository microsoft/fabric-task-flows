# Problem Statements for Stress Testing

> Auto-generated batch 13 — 50 problems for self-healing loop. Focus: data mesh, federated governance, event-driven architecture, ML feature engineering, graph analytics, temporal data, edge cases in phrasing.

## Data Architecture Patterns

1. "Each business unit owns their own data but we have no way to discover, access, or trust what other teams have produced."

2. "We want a federated approach where domain teams publish data products with documented schemas, SLAs, and quality guarantees."

3. "Our monolithic ETL pipeline has become impossible to maintain. Every change requires coordinating with five different teams."

4. "The data team is a bottleneck for every new analytical use case. We need to shift to a self-serve model where domain experts can build their own pipelines."

5. "We have a centralized warehouse that works for standard reporting but it can't keep up with the variety of analytical workloads different teams need."

## Event-Driven Architecture

6. "When a customer places an order, twelve different systems need to know about it. Right now we use point-to-point integrations and things constantly fall out of sync."

7. "We want to react to business events in real time rather than discovering problems in yesterday's batch reports."

8. "Our microservices communicate through a message broker but we have no way to replay or audit the event history."

9. "State changes in our CRM need to trigger downstream actions across marketing, billing, and customer success platforms."

10. "We need an event backbone that decouples producers from consumers so teams can evolve their systems independently."

## ML Feature Engineering & Serving

11. "Our data scientists spend 70% of their time preparing features instead of building models. Most of that work is duplicated across teams."

12. "Features computed for training don't match what's available at inference time, causing training-serving skew."

13. "We need a way to serve pre-computed features with sub-millisecond latency for our real-time recommendation engine."

14. "Model performance degrades silently over time because nobody monitors for data drift or concept drift."

15. "We want to run A/B tests on different model versions but we have no infrastructure for traffic splitting or metric comparison."

## Graph & Relationship Analytics

16. "We need to detect fraud rings by analyzing transaction networks — who sends money to whom, through which accounts, in what patterns."

17. "Our knowledge management system needs to surface related documents, experts, and prior decisions based on semantic similarity."

18. "We want to map the influence network in our organization to understand how information flows and where bottlenecks exist."

19. "Identifying beneficial ownership requires tracing through multiple layers of corporate structures, partnerships, and trusts."

20. "Our recommendation system needs to incorporate not just user preferences but also social connections and collaborative filtering signals."

## Temporal & Bi-Temporal Data

21. "We need to answer questions like 'what did we know about this customer as of last Tuesday' and 'when did we first learn their address changed'."

22. "Regulatory requirements demand that we reconstruct the exact state of our data as it existed at any point in the past five years."

23. "Price changes need to be tracked with both the effective date and the recording date so we can audit when corrections were made."

24. "Our SCD Type 2 implementation is creating performance problems as the dimension tables grow exponentially."

25. "We need to support both point-in-time queries for compliance and current-state queries for operations, ideally from the same data store."

## Subtle & Indirect Tech Intent

26. "The numbers in the executive dashboard don't match the numbers in the departmental reports and nobody can explain why."

27. "Our analysts discovered that the same customer appears in our database 17 times with slightly different name spellings."

28. "We signed a contract that requires us to respond to data subject access requests within 72 hours but our current process takes two weeks."

29. "The data team built a beautiful data warehouse but nobody uses it because the business users don't know it exists."

30. "Every month we manually stitch together data from our ERP, CRM, and HR system to produce the board report."

## Extremely Terse

31. "Stale dashboards."

32. "Pipeline spaghetti."

33. "Feature drift."

34. "Schema chaos."

35. "Metric disagreement."

## Compound Questions

36. "We need to figure out whether to build a centralized data platform or let each team manage their own — and if centralized, should it be a lakehouse or a traditional warehouse?"

37. "Should we invest in real-time capabilities now or wait until our batch processing is stable, and how do we evaluate the ROI of each approach?"

38. "Can we use the same data store for both our customer-facing application and our internal analytics, or do we need separate systems?"

39. "What's more important to tackle first: data quality issues that cause wrong numbers, or data access issues that prevent people from getting any numbers at all?"

40. "How do we balance the need for data governance and security with the demand for self-service analytics and data democratization?"

## Emerging Patterns

41. "We want to implement a data mesh but we're worried about the organizational change management required and whether our teams are ready."

42. "Our ML platform needs to support both traditional tabular models and LLM-based applications, including retrieval-augmented generation."

43. "We're exploring digital twins of our physical infrastructure and need to keep the virtual models synchronized with sensor data in near-real-time."

44. "The team wants to experiment with vector databases for semantic search but we need it to integrate with our existing analytics stack."

45. "We need a way to version both our data and our transformation logic so that any analytical result can be reproduced exactly."

## Edge Case Phrasing

46. "Nothing works and everything is on fire."

47. "We just need it to be fast."

48. "The data is fine, the problem is that nobody can access it."

49. "Our biggest challenge isn't technical — it's getting people to actually use the tools we've already built."

50. "We were told we need a data lakehouse but honestly we're not sure what that means or whether it's what we actually need."
