# Cloud Computing and Service Models

## Learning Objectives
- Define cloud computing via the five NIST characteristics.
- Contrast on-premise with cloud and the CapEx → OpEx shift.
- Distinguish deployment models: public, private, hybrid, multi-cloud.
- Compare service models IaaS vs PaaS vs SaaS and the shared responsibility boundary.
- Explain the main cloud pricing models and where each saves money.
- Recognize the recurring cloud challenges: security, cost, lock-in, governance.

## Why This Matters
Every modern data platform you will touch — including the BigQuery warehouse on Day 4 — runs in the cloud. Understanding the cloud is not optional background; it directly determines where your data lives, who is responsible for securing it, and how the bill is calculated. This note condenses the essential cloud vocabulary so that when you read "serverless PaaS with pay-per-query pricing," you know exactly what trade-offs that implies.

## Concept Explanation

### What Is Cloud Computing?
Cloud computing is the **on-demand delivery of computing resources** (servers, storage, databases, networking, software, analytics) **over the internet with pay-as-you-go pricing.** Instead of buying and running your own data center, you rent capability from a provider and pay for what you use.

NIST defines the cloud by **five essential characteristics** — a handy test for "is this really cloud?":
1. **On-demand self-service** — provision resources yourself, no human ticket to the provider.
2. **Broad network access** — reachable over the network via standard clients.
3. **Resource pooling** — provider serves many tenants from shared, multi-tenant infrastructure.
4. **Rapid elasticity** — scale up and down (often automatically) with demand.
5. **Measured service** — usage is metered, so you are billed precisely.

### On-Premise vs Cloud
The core economic shift is **CapEx → OpEx**: trade big upfront hardware purchases for ongoing pay-per-use spend.

| Aspect | On-premise | Cloud |
|--------|-----------|-------|
| Upfront cost | High (buy hardware) | Minimal |
| Ongoing cost | Lower, fixed | Pay-as-you-go, variable |
| Scaling | Limited by physical capacity | Near-unlimited, elastic |
| Maintenance | Your IT team | Provider-managed (mostly) |
| Deploy time | Weeks to months | Minutes to hours |
| Control | Full | Shared responsibility |

### Deployment Models — *where* the cloud runs
| Model | What it is | Best for | Trade-off |
|-------|-----------|----------|-----------|
| **Public** | Shared, provider-owned (AWS/Azure/GCP) | Startups, variable workloads, most use cases | Least control |
| **Private** | Single-tenant, dedicated to one org | Regulated industries, data sovereignty | Highest cost |
| **Hybrid** | Mix of public + private, data moves between | Cloud transitions, keep sensitive data on-prem | Complex to integrate |
| **Multi-cloud** | Multiple public providers at once | Avoid lock-in, best-of-breed services | Most operational complexity |

### Service Models — *how much* the provider manages
Think of a stack. The higher the model, the more the provider handles and the less you control.

```
              You manage        Provider manages
IaaS:  OS, runtime, apps, data        hardware, network, virtualization
PaaS:  apps, data                     + OS, runtime, middleware
SaaS:  data / config only             + everything else
```

| Aspect | IaaS | PaaS | SaaS |
|--------|------|------|------|
| You get | Virtual machines, storage, network | A platform to deploy code | Finished application |
| You manage | OS, runtime, app, data | App + data | Config + data |
| Control | High | Medium | Low |
| Effort / ops burden | High | Low | None |
| Examples | EC2, Compute Engine, Azure VMs | App Engine, Elastic Beanstalk, Cloud Functions | Gmail, Salesforce, Looker Studio |
| Data-world example | Self-managed Spark on VMs | **BigQuery** (serverless) | Tableau Online |

**Where does BigQuery fit?** It is effectively **serverless PaaS** — you bring SQL and data; Google manages all infrastructure, scaling, and tuning. This is why Day 4 needs no cluster setup.

**Shared responsibility model (crucial for data security):** the provider secures the layers it manages, you secure yours — but **you always own data security**, in every model.
```
Customer responsibility
   ^  IaaS: OS + runtime + apps + data
   |  PaaS: apps + data
   |  SaaS: data only
   +----------------------------------> Provider responsibility grows -->
```

### Pricing Models
Data workloads (variable compute, huge storage) are especially sensitive to pricing choices. The three cost dimensions are **compute**, **storage**, and **network (egress)**.

| Model | How it works | Savings | Best for |
|-------|--------------|---------|----------|
| **Pay-as-you-go / on-demand** | No commitment, billed per second/hour | Baseline (most expensive/unit) | Variable, dev/test, unpredictable |
| **Reserved / committed use** | Commit 1–3 years for a discount | ~30–60% | Steady, predictable production |
| **Spot / preemptible** | Rent spare capacity, can be reclaimed | Up to ~90% | Fault-tolerant batch, CI/CD |
| **Serverless / consumption** | Pay per query or per request | Pay only when used | Bursty analytics (e.g., BigQuery) |

Storage adds its own tiering (hot → nearline/cool → coldline → archive), cheaper the colder it gets — automated by lifecycle policies (see `302`). **Watch egress:** ingress (data in) is usually free, but data *leaving* the cloud or crossing regions is a frequently-overlooked cost.

BigQuery's pricing preview (detailed Day 4): on-demand **~$5 per TB scanned** plus ~$0.02/GB/month storage, or flat-rate slot capacity for predictable spend.

### Cloud Challenges
The benefits come with new problems to manage:

| Challenge | The risk | Mitigation |
|-----------|----------|------------|
| **Security & privacy** | Misconfigured buckets, weak IAM, breaches | Least-privilege IAM, encryption, MFA, audit logs |
| **Cost management** | Bill shock from zombies & egress | Budgets/alerts, right-sizing, lifecycle policies |
| **Vendor lock-in** | Hard/expensive to leave a provider | Open standards (Terraform, Kubernetes, SQL), export paths |
| **Compliance & governance** | HIPAA/GDPR/PCI obligations | Data classification, catalogs, region controls |
| **Operational complexity** | Fast-changing services, skills gap | Managed/serverless services, IaC, training |

## Code Example
Cloud resources are provisioned and used programmatically — the same idea across providers, different SDKs. A minimal GCS example (the storage you will pair with BigQuery on Day 4):

```python
from google.cloud import storage

client = storage.Client()

# Provision a bucket on-demand (self-service + elasticity in action).
bucket = client.create_bucket("my-data-bucket", location="us-central1")
print(f"Created gs://{bucket.name} in {bucket.location}")

# Upload an object — you pay per GB stored + per operation, not for a running server.
blob = bucket.blob("raw/sales.csv")
blob.upload_from_filename("sales.csv")
print("Uploaded gs://my-data-bucket/raw/sales.csv")

# Cost control: set a lifecycle rule so old data auto-moves to cheaper storage.
bucket.lifecycle_rules = [{
    "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
    "condition": {"age": 30},
}]
bucket.patch()
```

## Key Takeaways
- Cloud = on-demand, metered computing over the internet; the NIST five characteristics are the test.
- Cloud shifts spend from CapEx (buy hardware) to OpEx (pay-as-you-go).
- Deployment models (public/private/hybrid/multi-cloud) answer *where* it runs; service models (IaaS/PaaS/SaaS) answer *how much the provider manages*.
- Higher up the stack = less control, less effort. BigQuery is serverless PaaS.
- You always own data security under the shared responsibility model.
- Pricing: on-demand (flexible, pricey), reserved (predictable, ~30–60% off), spot (fault-tolerant, up to ~90% off), serverless (pay-per-use). Mind egress.
- Cloud challenges — security, cost, lock-in, governance, complexity — are all manageable with deliberate practices.

## Resources
- NIST cloud definition (SP 800-145): <https://csrc.nist.gov/publications/detail/sp/800-145/final>
- Cloud deployment models: <https://azure.microsoft.com/en-us/resources/cloud-computing-dictionary/what-are-private-public-hybrid-clouds/>
- IaaS/PaaS/SaaS explained: <https://azure.microsoft.com/en-us/resources/cloud-computing-dictionary/what-is-iaas-paas-saas/>
- GCP pricing calculator: <https://cloud.google.com/products/calculator>
- Sibling notes: `303-big-data-benefits-and-challenges`, `305-cloud-data-services-aws-azure-gcp`
