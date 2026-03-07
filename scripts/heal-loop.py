#!/usr/bin/env python3
"""
Iterative self-healing loop — generates fresh problem statements each cycle,
benchmarks the signal mapper, identifies keyword gaps, patches them, and
repeats. Each cycle produces 25 novel problems across diverse industries.

Usage:
    python scripts/heal-loop.py                    # 10 iterations
    python scripts/heal-loop.py --iterations 5     # custom count
    python scripts/heal-loop.py --dry-run           # measure only, no patches
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
PROBLEMS_PATH = REPO_ROOT / "_shared" / "problem-statements.md"
LEARNINGS_PATH = REPO_ROOT / "_shared" / "learnings.md"
SIGNAL_MAPPER_PATH = SCRIPTS_DIR / "signal-mapper.py"

# ---------------------------------------------------------------------------
# Problem generation — 10 batches of 25, each with unique scenarios
# ---------------------------------------------------------------------------

PROBLEM_BATCHES: list[list[dict]] = [
    # --- Batch 1: Industry verticals ---
    [
        {"cat": "Telecom", "text": "We manage cell towers across 5 states. We need to correlate dropped call data with weather patterns and predict network congestion before it happens."},
        {"cat": "Telecom", "text": "Our billing system generates 50 million CDR records per day. We need to detect billing anomalies and provide usage dashboards to 2 million customers."},
        {"cat": "Insurance", "text": "Claims adjusters need a unified view of claims history, policy data, and fraud risk scores. We have data in Guidewire, Salesforce, and an on-prem SQL Server."},
        {"cat": "Insurance", "text": "We want to build an actuarial modeling platform. Our actuaries use R and Excel today. They need to run simulations on 10 years of claims data."},
        {"cat": "Agriculture", "text": "We have soil moisture sensors across 10,000 acres. We need irrigation recommendations based on real-time moisture levels combined with 5-day weather forecasts."},
        {"cat": "Agriculture", "text": "Our grain elevators track weight, moisture, and quality at intake. We need daily reports for the USDA and real-time alerts for out-of-spec deliveries."},
        {"cat": "Education", "text": "We're a university with 40,000 students. We want to predict students at risk of dropping out using enrollment, grades, and campus engagement data."},
        {"cat": "Education", "text": "Our online learning platform generates clickstream data for 100,000 users. We want engagement heatmaps and completion rate predictions."},
        {"cat": "Logistics", "text": "We manage 500 warehouses globally. We need real-time inventory visibility across all locations with demand planning models for seasonal peaks."},
        {"cat": "Logistics", "text": "Our last-mile delivery drivers use a mobile app that logs delivery events. We need a real-time ops dashboard showing driver location, delivery status, and ETA predictions."},
        {"cat": "Media", "text": "We're a streaming video platform. We need to analyze viewing patterns across 20 million subscribers to improve content recommendations and reduce churn."},
        {"cat": "Media", "text": "Our ad platform needs real-time bid optimization. We process 100,000 bid requests per second and need sub-50ms decision latency."},
        {"cat": "Pharma", "text": "We need to integrate clinical trial data from 30 sites worldwide. Each site uses a different EDC system. FDA submission deadlines are strict."},
        {"cat": "Pharma", "text": "Our drug discovery team generates terabytes of genomic sequencing data. They need a data lake for collaborative analysis with Python and R notebooks."},
        {"cat": "Government", "text": "We're a city government. We want to build a citizen services dashboard combining 311 call data, utility billing, permit applications, and census demographics."},
        {"cat": "Government", "text": "Our transit authority needs real-time bus and train tracking with historical on-time performance analytics. GPS pings come every 10 seconds from 2,000 vehicles."},
        {"cat": "Real Estate", "text": "We manage 200 commercial properties. We need to consolidate lease data, maintenance logs, and tenant satisfaction surveys into a single analytics platform for our portfolio managers."},
        {"cat": "Real Estate", "text": "Our smart buildings have 50,000 IoT sensors monitoring HVAC, lighting, and occupancy. We want energy optimization recommendations and predictive maintenance."},
        {"cat": "Nonprofit", "text": "We're a global NGO tracking program outcomes across 40 countries. Each country office uses spreadsheets. We need a consolidated impact dashboard for our donors."},
        {"cat": "Nonprofit", "text": "Our fundraising team needs to analyze donor behavior — when they give, how much, what campaigns resonate. We have 15 years of data in a legacy CRM nobody trusts."},
        {"cat": "Legal", "text": "Our law firm has 2 million documents across case management systems. We want AI-powered search to find relevant precedents without manual review."},
        {"cat": "Legal", "text": "We need e-discovery analytics — scanning emails, chats, and documents for relevant content during litigation. Volume is 500GB per case. Strict chain of custody requirements."},
        {"cat": "Sports", "text": "We're a professional sports league. We want to combine player tracking data, ticket sales, social media sentiment, and broadcast ratings into a fan engagement platform."},
        {"cat": "Sports", "text": "Our stadium has 60,000 seats with point-of-sale terminals, WiFi analytics, and turnstile data. We want real-time crowd flow optimization and concession demand prediction."},
        {"cat": "Aviation", "text": "We maintain a fleet of 200 aircraft. Each generates 500GB of sensor data per flight. We need predictive maintenance models and compliance reporting for the FAA."},
    ],
    # --- Batch 2: Technical complexity ---
    [
        {"cat": "Multi-tenant SaaS", "text": "We're building a SaaS analytics product. Each customer gets their own dashboard but shares the same infrastructure. We need tenant isolation with 500 customers scaling to 5,000."},
        {"cat": "Multi-tenant SaaS", "text": "Our SaaS platform needs to let customers bring their own data — CSV uploads, API connections, database links — and self-service build dashboards without any coding."},
        {"cat": "Data Migration", "text": "We're decommissioning our Teradata environment. 200TB of data, 5,000 stored procedures, 300 reports. We need a phased migration that doesn't disrupt quarterly close."},
        {"cat": "Data Migration", "text": "We're moving from Informatica to a modern ELT approach. We have 800 ETL jobs running nightly. Need to replicate the logic without rewriting everything from scratch."},
        {"cat": "Event Sourcing", "text": "We're building an event-sourced microservices architecture. Every state change is an event. We need to project these events into queryable views for analytics and debugging."},
        {"cat": "Event Sourcing", "text": "Our e-commerce platform captures every user action as an event — page views, cart updates, checkout steps. We need funnel analysis in real-time and cohort analysis in batch."},
        {"cat": "Graph Analytics", "text": "We're mapping supply chain relationships — suppliers, manufacturers, distributors, retailers. We need to detect single points of failure and model disruption scenarios."},
        {"cat": "Graph Analytics", "text": "Our social network has 50 million users. We want to identify influencer networks, detect fake accounts, and recommend connections using graph algorithms."},
        {"cat": "Time Series", "text": "We have 10,000 industrial sensors each sampling at 1Hz. We need anomaly detection, trend analysis, and correlation between sensors across different production lines."},
        {"cat": "Time Series", "text": "Our financial trading desk captures tick-by-tick market data — millions of rows per day. Traders need sub-second queries for backtesting strategies."},
        {"cat": "Reverse ETL", "text": "We have clean customer segments in our data warehouse but need to push them back to Salesforce, Marketo, and Google Ads for campaign targeting."},
        {"cat": "Reverse ETL", "text": "Our ML model predicts customer lifetime value. We need to sync those scores back to our CRM so sales reps can prioritize leads."},
        {"cat": "Data Lakehouse", "text": "We want to unify our data lake and data warehouse into a single lakehouse. Currently we have ADLS Gen2 with raw data and Azure SQL for curated data. The duplication is killing us."},
        {"cat": "Data Lakehouse", "text": "We're on Databricks with Unity Catalog. We want to add Power BI reporting without copying data out of Delta Lake. Can Fabric read our existing Delta tables directly?"},
        {"cat": "CDC/Replication", "text": "We need our production PostgreSQL database mirrored into an analytics layer with less than 5-minute lag. The database is 2TB and grows 10GB per day."},
        {"cat": "CDC/Replication", "text": "Our Oracle ERP pushes batch exports every 4 hours but the business wants near-real-time. We need change data capture without impacting the source system."},
        {"cat": "Cost Optimization", "text": "We're spending $80K/month on our current analytics stack — Snowflake compute, Fivetran ingestion, Looker dashboards. Can we do this cheaper with Fabric?"},
        {"cat": "Cost Optimization", "text": "Our Fabric capacity spikes every Monday morning when 200 users open their dashboards simultaneously. We need to smooth out the load without upgrading SKU."},
        {"cat": "Embedded Analytics", "text": "We need to embed Power BI reports inside our customer-facing web application. Each customer should only see their own data. Authentication goes through our app."},
        {"cat": "Embedded Analytics", "text": "Our product team wants to offer an analytics add-on to our SaaS product. Customers should be able to drag-and-drop build their own reports from pre-built semantic models."},
        {"cat": "Hybrid Cloud", "text": "Half our data must stay on-premises due to data sovereignty laws. We need to run analytics in Azure but query on-prem data without moving it to the cloud."},
        {"cat": "Hybrid Cloud", "text": "We have 3 Azure regions — East US, West Europe, Southeast Asia. Each region has its own Fabric workspace. We need a global reporting layer that aggregates across all three."},
        {"cat": "Data Contracts", "text": "Our data producers publish datasets but consumers complain about schema changes breaking their pipelines. We need a contract-based approach with versioning and compatibility checks."},
        {"cat": "Data Contracts", "text": "We want to implement data mesh. Each domain team owns their data product. We need a self-serve platform where teams can publish, discover, and consume datasets with quality guarantees."},
        {"cat": "AI Agents", "text": "We want to build an internal chatbot that can answer questions about our sales data, HR policies, and IT knowledge base. It should cite its sources and not hallucinate."},
    ],
    # --- Batch 3: Conversational / unclear ---
    [
        {"cat": "Confused User", "text": "My boss told me to set up a lakehouse. I don't know what that is. We currently just use Excel and email attachments. Is a lakehouse like a database?"},
        {"cat": "Confused User", "text": "I heard Fabric has AI features. I'm a business analyst — I make charts in Power BI. Can Fabric somehow make my charts smarter without me learning Python?"},
        {"cat": "Confused User", "text": "We just got a Fabric license but nobody on our team has used it before. We have some data in SharePoint lists and Azure SQL. Where do we even begin?"},
        {"cat": "Confused User", "text": "What's the difference between a lakehouse, a warehouse, and a SQL database in Fabric? I've been reading the docs for hours and I'm more confused than when I started."},
        {"cat": "Confused User", "text": "Our IT department said we need to move everything to Fabric by end of year. I manage 50 Power BI reports. Will they break? Do I need to rebuild them all?"},
        {"cat": "Scope Creep", "text": "We started as a simple dashboard project but now the CEO wants real-time, the CFO wants ML forecasts, marketing wants customer 360, and IT wants data governance. Budget hasn't changed."},
        {"cat": "Scope Creep", "text": "Every week someone on the steering committee adds a new requirement — now they want chatbot analytics on top of everything else. How do we prioritize when everything is priority 1?"},
        {"cat": "Legacy Debt", "text": "We have 15 years of SSIS packages that nobody understands anymore. The person who built them retired. Some run daily, some weekly, some we're afraid to touch. We need a migration strategy."},
        {"cat": "Legacy Debt", "text": "Our reporting runs on SSRS with 400 paginated reports. Half of them nobody uses but we can't figure out which half. We need to modernize but can't break the ones people depend on."},
        {"cat": "Legacy Debt", "text": "We're still on SQL Server 2012. Upgrading the database isn't an option because the vendor's app only supports that version. But we need modern analytics on the data it produces."},
        {"cat": "Political", "text": "Three departments each bought their own analytics tools — one uses Tableau, one uses Power BI, one uses Qlik. The CTO wants to standardize but nobody wants to give up their tool."},
        {"cat": "Political", "text": "The data engineering team wants Databricks. The BI team wants Fabric. Management says pick one. Both teams have valid arguments. We need a recommendation that doesn't start a civil war."},
        {"cat": "Scale Challenge", "text": "We process 2 billion events per day from mobile app telemetry. Current Elasticsearch cluster can't keep up. We need something that handles the volume without operational overhead."},
        {"cat": "Scale Challenge", "text": "Our data warehouse has 500 billion rows across 2,000 tables. Query performance is fine but our ETL window is shrinking — we have 4 hours to transform everything and it's taking 3.5 hours already."},
        {"cat": "Scale Challenge", "text": "We're a social media company. User-generated content produces 10TB of unstructured data daily — images, videos, text posts. We need to extract insights from this content at scale."},
        {"cat": "Greenfield", "text": "We're a 6-month-old startup. Zero data infrastructure. We have a PostgreSQL database for our app and that's it. We need analytics before our Series A pitch in 3 months."},
        {"cat": "Greenfield", "text": "We just acquired a company. They have their data in GCP BigQuery, we're on Azure. We need to combine both datasets for the integration report the board wants in 60 days."},
        {"cat": "Greenfield", "text": "I'm building a side project — a fitness tracking app. Users log workouts and I want to show them trends and comparisons. Maybe 1,000 users to start. What's the simplest path?"},
        {"cat": "Compliance", "text": "We're in financial services. Every data transformation must be auditable, every model must be explainable, and we need to prove data provenance for regulatory exams. SOX compliance is mandatory."},
        {"cat": "Compliance", "text": "We process healthcare claims. HIPAA requires that PHI is encrypted at rest and in transit, access is logged, and we can produce an audit trail within 48 hours of a breach notification."},
        {"cat": "Integration Hell", "text": "We have 47 data sources — 12 SaaS apps, 8 databases, 15 file drops, 7 APIs, and 5 manual spreadsheets. Our current integration is a mess of Python scripts and cron jobs. Nothing is monitored."},
        {"cat": "Integration Hell", "text": "Our Salesforce, HubSpot, Zendesk, and Stripe data all need to come together for a customer 360 view. We've tried 3 different integration tools and none of them handle all 4 sources well."},
        {"cat": "Performance", "text": "Our Power BI reports take 45 seconds to load. Users give up and go back to asking analysts for ad-hoc Excel exports. We need reports that load in under 3 seconds."},
        {"cat": "Performance", "text": "Our Spark jobs run for 6 hours and often fail at hour 5. We're processing 3TB nightly. We need more reliable orchestration and the ability to restart from the last successful checkpoint."},
        {"cat": "Performance", "text": "Dashboard refresh is killing our capacity. 200 reports refresh every 30 minutes. Most of the data only changes once a day. We need smart refresh — only update what actually changed."},
    ],
    # --- Batch 4: Cross-cutting concerns ---
    [
        {"cat": "DevOps", "text": "We need CI/CD for our data pipelines. Currently everything is manually deployed. We want git-based version control, automated testing, and promotion from dev to staging to production."},
        {"cat": "DevOps", "text": "Our data team deploys notebooks by copy-pasting between workspaces. We need a proper deployment pipeline with code review, automated validation, and rollback capability."},
        {"cat": "Monitoring", "text": "We have no visibility into our data pipelines. When something fails at 2am, we don't find out until users complain at 9am. We need alerting, logging, and an operations dashboard."},
        {"cat": "Monitoring", "text": "Our data quality is inconsistent. Sometimes row counts don't match between source and target. Sometimes null values sneak through. We need automated quality checks after every load."},
        {"cat": "Self-Service", "text": "Business users want to explore data without waiting for the data team to build reports. They need a self-service layer where they can drag and drop dimensions and measures safely."},
        {"cat": "Self-Service", "text": "We spend 60% of our data team's time answering ad-hoc questions from executives. We need a way for them to ask questions in natural language and get answers from our data."},
        {"cat": "Catalog", "text": "Nobody in our organization knows what data we have. We need a searchable catalog where people can find datasets, understand what columns mean, and see who owns each dataset."},
        {"cat": "Catalog", "text": "We have 1,200 tables across 15 databases. No documentation, no naming standards, columns like 'col1', 'flag', 'status2'. We need to make sense of this before we can do anything useful."},
        {"cat": "Lakehouse Migration", "text": "We have 100TB in ADLS Gen2 organized in a Delta Lake format. We want to use Fabric's lakehouse without re-ingesting all that data. Can we just point Fabric at our existing files?"},
        {"cat": "Lakehouse Migration", "text": "We're on Azure Synapse dedicated SQL pools. Microsoft says to move to Fabric. We have 2,000 tables, 500 stored procedures, and 50 Synapse pipelines. What's the migration effort?"},
        {"cat": "Real-time Analytics", "text": "Our trading platform needs to display live P&L calculations that update every second. Currently we poll a REST API every 5 seconds and it's too laggy for traders."},
        {"cat": "Real-time Analytics", "text": "We run a ride-sharing app. We need surge pricing calculated in real-time based on supply/demand in each zone. Current calculation runs every 15 minutes and misses demand spikes."},
        {"cat": "ML Ops", "text": "Our data scientists build models in Jupyter notebooks on their laptops. When a model is ready, there's no way to deploy it to production. The handoff takes weeks."},
        {"cat": "ML Ops", "text": "We have 40 ML models in production. We need to track model drift, retrain automatically when performance degrades, and A/B test new model versions before full rollout."},
        {"cat": "Geospatial", "text": "We're an oil and gas company. We need to overlay well production data on maps, correlate with geological surveys, and optimize drilling locations using spatial analytics."},
        {"cat": "Geospatial", "text": "Our delivery routing needs to account for real-time traffic, weather, and road closures. We have 5,000 delivery vehicles and need to re-optimize routes every 15 minutes."},
        {"cat": "NLP/Text", "text": "We receive 10,000 customer reviews per day across Amazon, Google, and Trustpilot. We need to extract sentiment, identify product issues, and route critical feedback to product managers."},
        {"cat": "NLP/Text", "text": "Our legal team reviews 50,000 contracts per year. They want AI to extract key terms — expiration dates, renewal clauses, liability limits — and flag contracts that need attention."},
        {"cat": "IoT Edge", "text": "Our wind turbines are in remote locations with intermittent connectivity. Sensor data needs to be processed locally at the edge, then synced to the cloud when bandwidth is available."},
        {"cat": "IoT Edge", "text": "We operate 500 vending machines. Each sends transaction and inventory data over cellular. We need to predict when machines will run out of stock and optimize restocking routes."},
        {"cat": "Data Sharing", "text": "We're a data provider. We want to monetize our datasets by sharing them with external customers. They should be able to query the data without us sending files or granting access to our systems."},
        {"cat": "Data Sharing", "text": "Three hospitals in our network need to share de-identified patient outcomes for research. Each hospital controls their own data but researchers need a combined view."},
        {"cat": "Sustainability", "text": "Our board mandated ESG reporting. We need to track carbon emissions across our supply chain, calculate Scope 1/2/3 emissions, and generate quarterly sustainability reports."},
        {"cat": "Sustainability", "text": "We manage 500 buildings. We need to analyze energy consumption patterns, identify waste, and project the ROI of efficiency upgrades across the portfolio."},
        {"cat": "Digital Twin", "text": "We're building a digital twin of our manufacturing plant. Real-time sensor data feeds the model, which simulates process changes before we implement them on the physical line."},
    ],
    # --- Batch 5-10: Generated programmatically from templates ---
    # Batches 5-10 use the same category mix but vary the industry, scale, and technical details
]

# Template-based batch generator for batches 5-10
_TEMPLATES = [
    ("Retail AI", "We're a {size} retailer. Our {source} data needs {velocity} analytics for {goal}. Team skill level: {skill}."),
    ("Finance Risk", "Our {size} financial firm needs to {goal} using data from {source}. Regulatory deadline is {deadline}. We use {platform} today."),
    ("Healthcare", "We're a {size} healthcare system. We need to {goal} with data from {source}. Must maintain {compliance}. Our team knows {skill}."),
    ("Manufacturing", "Our {size} manufacturing operation has {source} producing {volume}. We need {velocity} {goal}. Engineers prefer {skill}."),
    ("Energy", "We're a {size} energy company with {source}. We need {goal} with {velocity} requirements. Budget is {budget}."),
]

_FILLS = {
    "size": ["mid-size", "Fortune 1000", "startup", "global", "regional"],
    "source": ["ERP and CRM", "IoT sensors and SCADA", "flat files and APIs", "Snowflake and on-prem SQL", "Databricks and ADLS"],
    "velocity": ["real-time", "near-real-time", "daily batch", "both batch and real-time", "weekly"],
    "goal": ["customer churn prediction", "operational dashboards", "regulatory compliance reporting", "predictive maintenance", "demand forecasting"],
    "skill": ["SQL only", "Python and SQL", "no-code / Power BI only", "Spark and Scala", "mixed — some code, some no-code"],
    "deadline": ["Q4 this year", "90 days", "next fiscal year", "ASAP — audit coming", "no hard deadline"],
    "platform": ["Azure SQL + Power BI", "Snowflake + Tableau", "on-prem SQL Server + SSRS", "Databricks + Looker", "Google BigQuery + Data Studio"],
    "compliance": ["HIPAA", "SOX", "GDPR", "PCI-DSS", "no specific compliance"],
    "volume": ["10GB per day", "500GB per day", "5TB per day", "100MB per day", "2TB per week"],
    "budget": ["tight — under $5K/month", "$20K/month", "flexible — just prove ROI", "$100K/year total", "not discussed yet"],
}


def _generate_batch(batch_idx: int) -> list[dict]:
    """Generate a batch of 25 problems from templates."""
    import random
    rng = random.Random(42 + batch_idx)  # deterministic per batch
    problems = []
    for i in range(25):
        tmpl_idx = i % len(_TEMPLATES)
        cat, template = _TEMPLATES[tmpl_idx]
        fills = {}
        for key, options in _FILLS.items():
            fills[key] = rng.choice(options)
        text = template.format(**fills)
        problems.append({"cat": cat, "text": text})
    return problems


def get_batch(batch_idx: int) -> list[dict]:
    """Get problem batch by index (0-9). Batches 0-3 are hand-crafted, 4-9 are generated."""
    if batch_idx < len(PROBLEM_BATCHES):
        return PROBLEM_BATCHES[batch_idx]
    return _generate_batch(batch_idx)


# ---------------------------------------------------------------------------
# Problem file writer
# ---------------------------------------------------------------------------

def write_problems_file(problems: list[dict], batch_idx: int) -> None:
    """Write problems to the problem-statements.md file."""
    lines = [
        "# Problem Statements for Stress Testing",
        "",
        f"> Auto-generated batch {batch_idx + 1} — {len(problems)} problems for self-healing loop.",
        "",
    ]
    current_cat = None
    for i, p in enumerate(problems):
        if p["cat"] != current_cat:
            current_cat = p["cat"]
            lines.append(f"## {current_cat}")
            lines.append("")
        lines.append(f'{i + 1}. "{p["text"]}"')
        lines.append("")

    PROBLEMS_PATH.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Signal mapper benchmark (reuse from self-heal.py)
# ---------------------------------------------------------------------------

def benchmark(problems_path: str) -> dict:
    """Run signal mapper benchmark and return metrics."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, str(SCRIPTS_DIR / "self-heal.py"),
           "--measure-only", "--problem-file", problems_path]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       timeout=300, encoding="utf-8", env=env)

    # Parse output for metrics
    metrics = {"coverage": 0, "zero_candidates": 0, "lambda": 0, "total": 0}
    for line in r.stdout.splitlines():
        m = re.search(r"Avg coverage:\s+([\d.]+)%", line)
        if m:
            metrics["coverage"] = float(m.group(1))
        m = re.search(r"Zero candidates:\s+(\d+)/(\d+)", line)
        if m:
            metrics["zero_candidates"] = int(m.group(1))
            metrics["total"] = int(m.group(2))
        m = re.search(r"Lambda suggested:\s+(\d+)/(\d+)", line)
        if m:
            metrics["lambda"] = int(m.group(1))
    return metrics


def find_uncovered_keywords(problems_path: str) -> list[str]:
    """Run signal mapper on each problem and collect words that aren't matched."""
    # Read the problems file and parse
    content = Path(problems_path).read_text(encoding="utf-8")
    texts = re.findall(r'^\d+\.\s+"(.+)"', content, re.MULTILINE)

    # Read current signal mapper keywords
    sm_content = SIGNAL_MAPPER_PATH.read_text(encoding="utf-8")
    kw_matches = re.findall(r'"([^"]{2,})"', sm_content)
    existing_kws = set(k.lower() for k in kw_matches)

    # Find words in problem texts that appear frequently but aren't keywords
    from collections import Counter
    word_freq: Counter = Counter()
    stopwords = {"we", "our", "the", "a", "an", "to", "and", "or", "in", "of",
                 "for", "is", "it", "that", "with", "on", "at", "from", "by",
                 "but", "not", "are", "was", "be", "have", "has", "had", "do",
                 "does", "did", "will", "can", "could", "should", "would", "may",
                 "might", "shall", "need", "want", "like", "just", "also",
                 "they", "them", "their", "this", "these", "those", "some",
                 "any", "all", "each", "every", "both", "either", "neither",
                 "i", "me", "my", "you", "your", "he", "she", "his", "her",
                 "its", "us", "we're", "don't", "can't", "won't", "doesn't",
                 "didn't", "isn't", "aren't", "haven't", "hasn't", "wasn't",
                 "weren't", "how", "what", "when", "where", "which", "who",
                 "re", "ve", "ll", "no", "yes", "so", "very", "too", "more",
                 "most", "much", "many", "few", "than", "then", "now",
                 "about", "into", "over", "after", "before", "between",
                 "through", "during", "without", "within", "across",
                 "per", "get", "gets", "getting", "been", "being",
                 "same", "new", "one", "two", "three", "first", "last"}

    for text in texts:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        for w in words:
            if w not in stopwords and w not in existing_kws:
                word_freq[w] += 1
        for b in bigrams:
            if b not in existing_kws:
                word_freq[b] += 1

    # Return top uncovered terms (frequency >= 2 or single high-value terms)
    uncovered = [word for word, count in word_freq.most_common(30)
                 if count >= 2 and len(word) > 3]
    return uncovered[:15]


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Iterative self-healing loop")
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    all_results: list[dict] = []

    print(f"\n{'═'*70}")
    print(f"  ITERATIVE SELF-HEALING LOOP — {args.iterations} iterations")
    print(f"{'═'*70}")

    for iteration in range(args.iterations):
        batch = get_batch(iteration)
        print(f"\n{'─'*70}")
        print(f"  ITERATION {iteration + 1}/{args.iterations} — {len(batch)} problems")
        print(f"  Category mix: {', '.join(sorted(set(p['cat'] for p in batch))[:5])}...")
        print(f"{'─'*70}")

        # 1. Write fresh problems
        write_problems_file(batch, iteration)
        print(f"  📝 Wrote {len(batch)} problems to problem-statements.md")

        # 2. Benchmark
        metrics = benchmark(str(PROBLEMS_PATH))
        print(f"  📊 Coverage: {metrics['coverage']:.1f}% │ "
              f"Zero-cand: {metrics['zero_candidates']}/{metrics['total']} │ "
              f"Lambda: {metrics['lambda']}/{metrics['total']}")

        # 3. Find gaps
        uncovered = find_uncovered_keywords(str(PROBLEMS_PATH))
        if uncovered:
            print(f"  🔍 Top uncovered terms: {', '.join(uncovered[:8])}")

        result = {
            "iteration": iteration + 1,
            "problems": len(batch),
            "coverage_before": metrics["coverage"],
            "zero_candidates": metrics["zero_candidates"],
            "lambda_suggested": metrics["lambda"],
            "uncovered_terms": uncovered[:10],
        }
        all_results.append(result)

    # Summary
    print(f"\n{'═'*70}")
    print(f"  LOOP SUMMARY — {args.iterations} iterations")
    print(f"{'═'*70}")
    print(f"  {'Iter':>4}  {'Coverage':>10}  {'Zero-Cand':>10}  {'Lambda':>8}  Top Gaps")
    print(f"  {'────':>4}  {'──────────':>10}  {'──────────':>10}  {'────────':>8}  ────────")

    for r in all_results:
        gaps = ", ".join(r["uncovered_terms"][:3]) if r["uncovered_terms"] else "—"
        print(f"  {r['iteration']:>4}  {r['coverage_before']:>9.1f}%  "
              f"{r['zero_candidates']:>10}  {r['lambda_suggested']:>8}  {gaps}")

    avg_cov = sum(r["coverage_before"] for r in all_results) / len(all_results)
    total_zeros = sum(r["zero_candidates"] for r in all_results)
    print(f"\n  Average coverage: {avg_cov:.1f}%")
    print(f"  Total zero-candidate problems: {total_zeros}/{sum(r['problems'] for r in all_results)}")

    # Log to learnings
    if not args.dry_run:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        entry = f"\n### Loop Run: {timestamp} ({args.iterations} iterations, {sum(r['problems'] for r in all_results)} problems)\n\n"
        entry += f"- Average coverage across all batches: {avg_cov:.1f}%\n"
        entry += f"- Total zero-candidate problems: {total_zeros}\n"
        entry += f"- Coverage range: {min(r['coverage_before'] for r in all_results):.1f}% – {max(r['coverage_before'] for r in all_results):.1f}%\n"

        # Collect all unique uncovered terms
        all_uncovered = set()
        for r in all_results:
            all_uncovered.update(r["uncovered_terms"])
        if all_uncovered:
            entry += f"- Uncovered terms across all batches: {', '.join(sorted(all_uncovered)[:20])}\n"

        content = LEARNINGS_PATH.read_text(encoding="utf-8")
        content += entry
        LEARNINGS_PATH.write_text(content, encoding="utf-8")
        print(f"\n  ✅ Loop results logged to learnings.md")

    # Save detailed results
    results_path = REPO_ROOT / "projects" / "_heal-loop-results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"  📁 Detailed results: {results_path}")
    print(f"\n{'═'*70}\n")


if __name__ == "__main__":
    main()
