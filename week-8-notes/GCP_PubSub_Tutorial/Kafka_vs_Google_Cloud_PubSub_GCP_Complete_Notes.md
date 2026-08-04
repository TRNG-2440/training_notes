# Kafka vs Google Cloud Pub/Sub (GCP)

## Complete Fresher-Friendly Notes for Data Engineering

------------------------------------------------------------------------

# Learning Objectives

After completing this topic, you should be able to answer:

-   What is Apache Kafka?
-   What is Google Cloud Pub/Sub?
-   Why do both exist?
-   When should we choose Kafka?
-   When should we choose Pub/Sub?
-   What are their similarities?
-   What are their differences?
-   Which companies generally use Kafka and which use Pub/Sub?
-   Interview questions and answers.

------------------------------------------------------------------------

# Real-World Story

Imagine an international e-commerce company.

Customers\
↓\
Website\
↓\
Orders Generated

Many systems need the order:

-   Inventory
-   Payment
-   Shipping
-   Email Notification
-   Analytics
-   Fraud Detection

The challenge is:

How can one order be sent to many systems simultaneously?

This is where **Messaging Systems** come in.

Two popular solutions are:

1.  Apache Kafka
2.  Google Cloud Pub/Sub

------------------------------------------------------------------------

# What is Apache Kafka?

Apache Kafka is an **open-source distributed event streaming platform**.

Applications write events into Kafka Topics, and consumers read them
independently.

Common use cases:

-   High-speed streaming
-   Event-driven architectures
-   Log aggregation
-   Data pipelines
-   Real-time analytics

``` text
Producer
   |
   v
+--------------+
| Kafka Topic  |
+--------------+
| Partition 1  |
| Partition 2  |
| Partition 3  |
+--------------+
  |    |    |
  v    v    v
Consumer A
Consumer B
Consumer C
```

------------------------------------------------------------------------

# What is Google Cloud Pub/Sub?

Google Cloud Pub/Sub is Google's **fully managed messaging service**.

You only create Topics and Subscriptions. Google manages:

-   Infrastructure
-   Scaling
-   Replication
-   High Availability
-   Maintenance

``` text
Publisher
    |
    v
+----------+
|  Topic   |
+----------+
 |   |   |
 v   v   v
Sub1 Sub2 Sub3
 |     |     |
SvcA SvcB  SvcC
```

------------------------------------------------------------------------

# Why Messaging Systems?

Without messaging:

``` text
Order Service
   |
---------------------------------
|  |   |    |      |
Inv Pay Ship Mail Analytics
```

Problems:

-   Tight coupling
-   Slow downstream systems affect upstream systems
-   Difficult to add new consumers

With messaging:

``` text
Order Service
      |
      v
 Messaging Platform
      |
-----------------------------
|   |    |    |      |
Inv Ship Mail Fraud Analytics
```

Each consumer works independently.

------------------------------------------------------------------------

# Kafka vs Pub/Sub Overview

  Kafka                         Google Cloud Pub/Sub
  ----------------------------- -------------------------------
  Open Source                   Fully Managed
  Install & Manage Yourself     No Installation
  Stores Events                 Delivers Events
  Full Infrastructure Control   Google Manages Infrastructure

------------------------------------------------------------------------

# Deployment

## Kafka

You manage:

-   Brokers
-   Storage
-   Replication
-   Upgrades
-   Monitoring
-   Scaling

## Pub/Sub

Google manages everything.

You simply:

1.  Create Topic
2.  Create Subscription
3.  Publish
4.  Consume

------------------------------------------------------------------------

# Message Storage

## Kafka

-   Long configurable retention
-   Replay historical events
-   Consumers control offsets

## Pub/Sub

-   Configurable retention for reliable delivery
-   Supports replay within retention window
-   Optimized for message delivery

------------------------------------------------------------------------

# Ordering

## Kafka

Ordering guaranteed within a partition.

## Pub/Sub

Ordering supported using Ordering Keys.

------------------------------------------------------------------------

# Scalability

## Kafka

Manual cluster expansion.

## Pub/Sub

Automatic scaling handled by Google.

------------------------------------------------------------------------

# Security

## Kafka

Configure manually:

-   SSL
-   SASL
-   ACLs

## Pub/Sub

Integrated with:

-   IAM
-   Service Accounts
-   Cloud Audit Logs
-   Encryption

------------------------------------------------------------------------

# Monitoring

Kafka:

-   Prometheus
-   Grafana
-   JMX

Pub/Sub:

-   Cloud Monitoring
-   Cloud Logging
-   Cloud Audit Logs

------------------------------------------------------------------------

# Real-World Example

## Kafka

Customer Order

↓

Kafka Topic

↓

Inventory

Shipping

Analytics

Fraud Detection

Recommendation Engine

Historical replay available.

## Pub/Sub

Customer Order

↓

Pub/Sub Topic

↓

Cloud Run

Cloud Functions

BigQuery

Dataflow

Auto scales automatically.

------------------------------------------------------------------------

# When to Choose Kafka

Choose Kafka if:

-   Need event replay
-   Multi-cloud
-   On-premises
-   High throughput streaming
-   Long-term retention
-   Fine-grained control

------------------------------------------------------------------------

# When to Choose Pub/Sub

Choose Pub/Sub if:

-   Working mainly in GCP
-   Want serverless architecture
-   Need automatic scaling
-   Prefer no infrastructure management
-   Integrating with Dataflow or BigQuery

------------------------------------------------------------------------

# Feature Comparison

  Feature          Kafka                      Pub/Sub
  ---------------- -------------------------- -------------------------
  Type             Event Streaming Platform   Managed Messaging
  Installation     Required                   None
  Scaling          Manual                     Automatic
  Replay           Excellent                  Within retention window
  Ordering         Per Partition              Ordering Keys
  Infrastructure   Self Managed               Google Managed
  Best For         Streaming Platforms        Cloud Native Apps

------------------------------------------------------------------------

# Decision Flow

``` text
Need infrastructure control?
        |
      Yes ---> Kafka
        |
       No
        |
Using GCP?
        |
      Yes ---> Pub/Sub
        |
       No
        |
Need long-term replay?
        |
      Yes ---> Kafka
        |
       No ---> Pub/Sub
```

------------------------------------------------------------------------

# Advantages

## Kafka

-   Open source
-   Vendor independent
-   Excellent replay
-   High throughput
-   Large ecosystem

## Pub/Sub

-   Fully managed
-   Auto scaling
-   Easy integration
-   High availability
-   Minimal operations

------------------------------------------------------------------------

# Limitations

## Kafka

-   Operational complexity
-   Cluster management
-   Capacity planning

## Pub/Sub

-   GCP ecosystem dependency
-   Less infrastructure control

------------------------------------------------------------------------

# Interview Questions

### What is the primary difference?

Kafka is a distributed event streaming platform. Pub/Sub is a managed
messaging service.

### Which supports replay better?

Kafka.

### Which requires brokers?

Kafka.

### Which requires installation?

Kafka.

### Which is easier to manage?

Pub/Sub.

### Which integrates best with Dataflow?

Pub/Sub.

### Can Kafka run on-premises?

Yes.

### Which is better for GCP-native applications?

Pub/Sub.

------------------------------------------------------------------------

# Summary

  Choose Kafka             Choose Pub/Sub
  ------------------------ -------------------
  Event Streaming          Managed Messaging
  Replay                   Easy Operations
  Multi-cloud              GCP Native
  Infrastructure Control   Automatic Scaling

## Key Takeaway

**Kafka** is best when you need a durable event streaming platform with
replay and infrastructure control.

**Google Cloud Pub/Sub** is best when you want a fully managed, scalable
messaging service tightly integrated with Google Cloud.
