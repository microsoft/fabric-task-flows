## Discovery Brief

**Project:** Campaign Command
**Date:** 2026-03-09

### Problem Statement

> Marketing company needs to ingest Google Analytics, AdWords, and social media data. Real-time social sentiment monitoring and influencer content amplification — speed to share is EXTREMELY important. Batch ROI reporting for regional ad buy optimization across the US (turn the firehose up or slow down based on ROI). Internal exec chatbot for self-service campaign performance Q&A. Code-first shop, $500k ad spend, expect high volume. Want a solid, scalable solution with minimal complexity.

### Inferred Signals

| Signal | Value | Confidence | Source |
|--------|-------|------------|--------|
| Real-time / Streaming | Social sentiment + content amplification | High | "speed to share is EXTREMELY important" |
| Batch / Scheduled | Analytics, AdWords, ROI reporting | High | Google Analytics, AdWords imports |
| Both / Mixed (Lambda) | Batch analytics + real-time social | High | Dual velocity clearly stated |
| Machine Learning | Sentiment analysis, regional ROI optimization | Medium | Ad buy automation, sentiment |
| Unstructured Data | Social media posts, influencer content | Medium | Sentiment + resharing use case |
| Semantic / AI Layer | Exec chatbot via Data Agent | High | "leave us alone" self-service bot |

### 4 V's Assessment

| V | Value | Confidence | Source |
|---|-------|------------|--------|
| Volume | Medium-High (scaling with $500k spend) | Medium | "expect it to be huge" |
| Velocity | Mixed — batch + real-time | High | Dual pattern stated |
| Variety | High — Analytics, AdWords, social APIs, text | High | 4+ source types named |
| Versatility | Code-first | High | "code first shop for sure" |

### Suggested Task Flow Candidates

| Candidate | Why It Fits | Confidence |
|-----------|-------------|------------|
| lambda | Batch analytics + real-time social in one arch | High |
| event-medallion | Streaming-heavy alternative with quality layers | Medium |
| basic-machine-learning-models | Complement for sentiment/ROI models | Medium |
| conversational-analytics | Overlay for exec chatbot via Data Agent | High |

### Confirmed with User

- [x] Project name confirmed: "Campaign Command"
- [x] Signals confirmed — user validated all inferences
- [x] Volume: $500k spend, expect large scale
- [x] Versatility: code-first confirmed
- [x] Chatbot scope: internal exec self-service only
- [x] Data Agent is GA (user corrected from Preview)
- [x] User Data Functions is GA (user corrected from Preview)

### Architectural Judgment Calls

- Integration-first: Google/social platforms stay external; Fabric ingests via APIs
- Chatbot → Semantic Model + Data Agent, not customer-facing bot
- "Dashboard" → Reports (batch ROI) + Real-Time Dashboard (social stream)
- Regional ad optimization implies geo-partitioned aggregation layer
- conversational-analytics overlays primary flow, does not replace it
