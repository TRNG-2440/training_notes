# Apache Kafka — Data Engineering Tutorial

## 1. What is Apache Kafka?

**Apache Kafka is an open-source, distributed event-streaming platform.** It is used to collect, store, transport, and process continuously generated data called **events** or **messages**.

Examples of events include:

- A customer placing an order
- A credit-card payment
- A driver-location update
- A website click
- A machine-temperature reading
- An application log entry
- A database row being inserted or updated

### Simple definition

> Kafka acts as a high-speed, reliable middle layer that carries data from systems producing it to systems that need to process it.

---

## 2. Simple Real-World Analogy

Think of Kafka as a **railway parcel distribution centre**.

- Applications sending parcels are **producers**.
- The distribution centre is the **Kafka cluster**.
- Different parcel categories are **topics**.
- Separate conveyor belts are **partitions**.
- Delivery teams collecting parcels are **consumers**.
- The parcel tracking number is the **offset**.

Kafka stores events for a configured period, so consumers can process them immediately or read them again later.

Multiple independent consumer groups can read the same topic for different purposes.

---

## 3. Why Do We Use Kafka?

### Problem Without Kafka

Imagine an online food-delivery application with these systems:

- Customer application
- Payment service
- Restaurant service
- Driver-assignment service
- Notification service
- Analytics platform
- Data warehouse

Without Kafka, the order application might directly call every downstream system:

```text
Order Application
   ├── Payment Service
   ├── Restaurant Service
   ├── Driver Service
   ├── Notification Service
   ├── Analytics System
   └── Data Warehouse
```

This creates several problems:

- Systems become tightly connected.
- One unavailable service may affect the entire transaction flow.
- Sudden traffic can overload downstream systems.
- Adding another consumer requires changing the source application.
- Recovering missed data becomes difficult.

### Solution With Kafka

```text
                         ┌── Payment Service
                         ├── Restaurant Service
Order Application        ├── Driver Service
      │                  ├── Notification Service
      ▼                  ├── Spark Streaming
 Kafka Topic ────────────┼── Fraud Detection
   orders                ├── Data Lake
                         └── Data Warehouse
```

The order application publishes the event once.

Each downstream application consumes it independently.

Kafka provides:

- Loose coupling
- Event buffering
- Parallel processing
- Scalability
- Fault tolerance
- Event replay

---

# 4. Important Kafka Components

## 4.1 Producer

A **producer** is an application that sends events to Kafka.

Examples:

- Customer application sends an `ORDER_CREATED` event.
- Payment service sends a `PAYMENT_COMPLETED` event.
- IoT device sends a `TEMPERATURE_READING` event.
- Database CDC tool sends an `EMPLOYEE_UPDATED` event.

```text
Mobile Application
       │
       │ ORDER_CREATED
       ▼
     Kafka
```

---

## 4.2 Event or Message

An **event** represents something that happened.

```json
{
  "event_id": "EVT-10001",
  "event_type": "ORDER_CREATED",
  "order_id": "ORD-501",
  "customer_id": "CUS-110",
  "restaurant_id": "RES-25",
  "city": "Bengaluru",
  "amount": 28.50,
  "event_time": "2026-07-27T10:30:00Z"
}
```

A Kafka event normally contains:

- Key
- Value
- Timestamp
- Optional headers
- Topic
- Partition
- Offset

---

## 4.3 Topic

A **topic** is a logical category used to organise related events.

Examples:

```text
orders
payments
driver-locations
customer-clicks
application-logs
inventory-updates
```

### Example

```text
Topic: orders

ORDER_CREATED
RESTAURANT_ACCEPTED
DRIVER_ASSIGNED
ORDER_DELIVERED
```

A topic can have:

- Multiple producers
- Multiple consumers
- Multiple partitions

---

## 4.4 Partition

A topic is divided into one or more **partitions**.

```text
Topic: orders

Partition 0: ORD-100, ORD-103, ORD-106
Partition 1: ORD-101, ORD-104, ORD-107
Partition 2: ORD-102, ORD-105, ORD-108
```

Partitions provide:

- Parallel processing
- Horizontal scalability
- Load distribution
- Ordering within an individual partition

Kafka guarantees ordering **within a partition**, but not automatically across all partitions.

### Partition Key Example

Use `order_id` as the event key:

```text
Key = ORD-1001
```

All events for `ORD-1001` can be written to the same partition:

```text
ORDER_CREATED
PAYMENT_COMPLETED
RESTAURANT_ACCEPTED
DRIVER_ASSIGNED
ORDER_DELIVERED
```

This preserves the event order for that order.

---

## 4.5 Broker

A **broker** is a Kafka server.

A production Kafka environment normally contains multiple brokers.

```text
Kafka Cluster
 ├── Broker 1
 ├── Broker 2
 └── Broker 3
```

Topic partitions are distributed across brokers.

Kafka can replicate partitions across different brokers so data remains available when a broker fails.

---

## 4.6 Consumer

A **consumer** reads events from Kafka.

Examples:

- Spark reads orders for real-time analytics.
- Notification service sends customer messages.
- Fraud system checks suspicious payments.
- Data-lake loader stores raw events.
- Dashboard application calculates live metrics.

```text
Kafka orders topic
      │
      ▼
Spark Structured Streaming
      │
      ▼
Live Order Dashboard
```

---

## 4.7 Consumer Group

Consumers can work together as a **consumer group**.

```text
Topic: orders
Partitions: P0, P1, P2

Consumer Group: analytics-group

Consumer 1 → P0
Consumer 2 → P1
Consumer 3 → P2
```

Within one consumer group:

- Each partition is processed by one consumer at a time.
- Consumers share the processing workload.
- If a consumer fails, partitions are reassigned.

Different consumer groups can independently read the same topic.

```text
orders topic
   ├── notification-group
   ├── analytics-group
   ├── fraud-group
   └── data-lake-group
```

---

## 4.8 Offset

An **offset** identifies an event's position inside a partition.

```text
Partition 0

Offset 0 → ORDER_CREATED
Offset 1 → PAYMENT_COMPLETED
Offset 2 → RESTAURANT_ACCEPTED
Offset 3 → DRIVER_ASSIGNED
```

A consumer tracks its progress using offsets.

Offsets make it possible to:

- Resume processing
- Replay old events
- Rebuild output
- Recover after failure

---

## 4.9 Replication

Replication creates copies of a partition across brokers.

```text
Partition P0

Broker 1 → Leader
Broker 2 → Replica
Broker 3 → Replica
```

The leader handles reads and writes.

Follower replicas copy the leader's data.

If the leader broker fails, an eligible replica can become the new leader.

---

# 5. End-to-End Real-World Example

## Food-Delivery Order Processing

Assume a customer places an order through a food-delivery application.

### Step 1: Customer Places the Order

The customer application creates an event:

```json
{
  "event_type": "ORDER_CREATED",
  "order_id": "ORD-9001",
  "customer_id": "CUS-501",
  "restaurant_id": "RES-42",
  "amount": 35.75,
  "city": "Bengaluru"
}
```

### Step 2: Producer Sends the Event

```text
Customer Application
        │
        ▼
Kafka Producer
        │
        ▼
Topic: orders
```

### Step 3: Kafka Stores the Event

Kafka places the event in one partition of the `orders` topic.

```text
Topic: orders

Partition 0 → ORD-9000
Partition 1 → ORD-9001
Partition 2 → ORD-9002
```

### Step 4: Multiple Consumers Process the Event

```text
                           ┌── Restaurant Service
                           │   Accepts the order
                           │
                           ├── Payment Service
                           │   Processes payment
orders topic ──────────────┤
                           ├── Notification Service
                           │   Sends confirmation
                           │
                           ├── Spark Streaming
                           │   Calculates live sales
                           │
                           └── Data Lake Loader
                               Stores raw history
```

### Step 5: Spark Performs Streaming Transformation

```text
Read orders
     ↓
Validate schema
     ↓
Remove invalid records
     ↓
Calculate sales by city
     ↓
Write results to Delta Lake
     ↓
Update live dashboard
```

### Step 6: Operations Dashboard Updates

```text
Bengaluru

Active orders: 1,250
Completed orders: 8,420
Delayed orders: 73
Current sales: $248,500
```

This is a real-time data pipeline:

1. Applications publish events.
2. Kafka stores and distributes events.
3. Processing systems transform or react to events.
4. Results are written to dashboards, databases, or data lakes.

---

# 6. How Kafka Helps in Data Engineering

## 6.1 Real-Time Data Ingestion

Kafka can continuously collect data from:

- Databases
- Mobile applications
- Web applications
- Microservices
- Sensors
- Log files
- Cloud services
- Payment systems

```text
Databases ─────┐
Applications ──┤
Sensors ───────┼── Kafka ── Data Engineering Pipeline
Logs ──────────┤
APIs ──────────┘
```

---

## 6.2 Decoupling Source and Destination Systems

The producer does not need to know every destination.

### Before Kafka

```text
Application → Database
Application → Dashboard
Application → Spark
Application → Notification
Application → Data Warehouse
```

### With Kafka

```text
Application → Kafka → Multiple destinations
```

This simplifies integration and allows new consumers to be added without redesigning every producer.

---

## 6.3 Buffering Sudden Data Volume

Suppose a shopping website normally receives:

```text
1,000 events per second
```

During a major sale, it receives:

```text
50,000 events per second
```

Kafka stores the incoming events while downstream consumers process them at their own available speed.

This prevents a slow consumer from immediately blocking the producer.

---

## 6.4 Building Bronze, Silver, and Gold Pipelines

Kafka fits naturally into a medallion-style data platform.

```text
Applications and Databases
            │
            ▼
          Kafka
            │
            ▼
Bronze Layer
Raw Kafka events
            │
            ▼
Silver Layer
Cleaned, validated and deduplicated data
            │
            ▼
Gold Layer
Aggregations and business reports
```

### Bronze Layer

Store the event exactly or nearly exactly as received.

```text
order_id | event_type    | city      | amount
ORD-101  | ORDER_CREATED | Bengaluru | 28.50
```

### Silver Layer

Perform:

- Schema validation
- Null-value handling
- Type conversion
- Deduplication
- Standardisation
- Filtering

### Gold Layer

Create:

- Sales by city
- Orders by hour
- Delayed-order report
- Restaurant performance report
- Customer-order summary

---

## 6.5 Integration With Stream-Processing Systems

Kafka frequently provides input and output topics for stream-processing pipelines.

```text
Kafka
  │
  ▼
Spark Structured Streaming
  │
  ├── Clean
  ├── Filter
  ├── Join
  ├── Aggregate
  └── Detect anomalies
  │
  ▼
Delta Lake / Database / Dashboard
```

---

## 6.6 Change Data Capture

Kafka can be used as part of a Change Data Capture pipeline.

```text
Operational Database
        │
        │ Insert / Update / Delete
        ▼
    CDC Connector
        │
        ▼
      Kafka
        │
        ▼
Data Lake / Warehouse / Search System
```

For example, when a customer record changes in an operational database, the change can be published as an event and delivered to analytics and reporting systems.

---

## 6.7 Replay and Reprocessing

Kafka stores events according to a configured retention period.

A consumer can read earlier events again by resetting its offset.

This is helpful when:

- Business logic changes
- A processing job fails
- A new destination is added
- Historical aggregates must be rebuilt
- A bug produced incorrect output

```text
Stored Kafka Events
        │
        ├── Original processing
        └── Replay after code correction
```

---

## 6.8 Multiple Destinations From One Source

The same event can serve multiple data-engineering and business requirements.

```text
Kafka payment-events
     ├── Fraud detection
     ├── Customer notification
     ├── Financial reporting
     ├── Data lake
     ├── Monitoring dashboard
     └── Machine-learning features
```

Each destination can use a separate consumer group.

---

# 7. Kafka Data Engineering Architecture

```text
┌───────────────────────────────────────────────┐
│                Data Sources                   │
│ Applications | Databases | APIs | IoT | Logs │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│                 Kafka Cluster                 │
│                                               │
│ Topics                                        │
│ ├── orders                                    │
│ ├── payments                                  │
│ ├── inventory                                 │
│ └── customer-events                           │
│                                               │
│ Partitions + Replication + Event Retention    │
└──────────────────────┬────────────────────────┘
                       │
          ┌────────────┼─────────────┐
          ▼            ▼             ▼
┌──────────────┐ ┌───────────┐ ┌───────────────┐
│ Spark/Flink  │ │ Data Lake │ │ Microservices │
│ Processing   │ │ Raw Data  │ │ Notifications │
└──────┬───────┘ └───────────┘ └───────────────┘
       │
       ▼
┌───────────────────────────────────────────────┐
│             Analytics Destinations            │
│ Delta Lake | Warehouse | BI | ML | Alerts    │
└───────────────────────────────────────────────┘
```

---

# 8. Kafka Connect

**Kafka Connect** is a Kafka component used to move data between Kafka and external systems using reusable connectors.

## Source Connector

Moves data **into Kafka**.

```text
MySQL → Kafka
PostgreSQL → Kafka
Application Logs → Kafka
Cloud Storage → Kafka
```

## Sink Connector

Moves data **from Kafka** to another system.

```text
Kafka → Data Lake
Kafka → Search Engine
Kafka → Database
Kafka → Cloud Storage
```

Kafka Connect reduces the need to write custom producer and consumer programs for common integrations.

---

# 9. Kafka vs Traditional Database

| Area | Kafka | Traditional Database |
|---|---|---|
| Main purpose | Event streaming and transport | Persistent business-data management |
| Data model | Append-oriented event log | Tables, documents, or records |
| Processing style | Continuous | Queries and transactions |
| Data consumption | Consumers read by offset | Users query current stored state |
| Replay | Natural use case | Usually requires history or audit tables |
| Typical role | Movement and distribution of events | System of record or analytical storage |

Kafka is usually not a replacement for an operational database or a data warehouse.

Kafka connects systems and transports events to the appropriate processing and storage destinations.

---

# 10. Kafka vs Simple Message Queue

| Feature | Basic Message Queue | Kafka |
|---|---|---|
| Message retention | Often removed after acknowledgement | Retained based on policy |
| Replay | Usually limited | Consumers can read earlier offsets |
| Parallelism | Queue consumers | Topic partitions and consumer groups |
| Multiple use cases | Primarily message delivery | Event streaming, integration, and pipelines |
| Historical consumption | Not always central | Core design capability |
| Large-scale analytics pipelines | Limited | Common use case |

---

# 11. Advantages of Kafka

Kafka is especially useful when a system requires:

- Continuous event ingestion
- High throughput
- Low-latency delivery
- Horizontal scaling through partitions
- Fault tolerance through replication
- Independent downstream consumers
- Data replay
- Real-time analytics
- Event-driven microservices
- Integration between many data systems

---

# 12. Challenges and Considerations

## 12.1 Partition-Key Selection

A poor partition key may send most events to one partition.

```text
Bad distribution:

Partition 0: 90% of events
Partition 1: 5%
Partition 2: 5%
```

This is called a **hot partition**.

Choose a key that distributes events evenly while preserving required ordering.

---

## 12.2 Duplicate Handling

Duplicate events can occur because of:

- Producer retries
- Consumer retries
- At-least-once delivery
- Job restarts

Use:

- Unique event IDs
- Deduplication logic
- Idempotent writes
- Transactional processing where suitable

---

## 12.3 Schema Evolution

Changing an event structure without coordination can break consumers.

Good practices include:

- Schema Registry
- Backward-compatible changes
- Versioned schemas
- Optional fields
- Data contracts

---

## 12.4 Ordering

Kafka guarantees ordering only within a partition.

Use the same event key when related events must remain ordered.

---

## 12.5 Monitoring

Teams should monitor:

- Producer errors
- Consumer lag
- Broker availability
- Partition distribution
- Disk usage
- Processing throughput
- Failed or malformed events

---

# 13. One-Line Interview Explanation

> Apache Kafka is a distributed event-streaming platform that allows producers to publish events into partitioned topics and multiple consumer groups to process those events independently, making it useful for scalable, fault-tolerant, real-time data-engineering pipelines.

---

# 14. Interview Scenario

## Question

How would you use Kafka in an online retail data platform?

## Answer

The retail website publishes order, payment, inventory, and customer-click events to separate Kafka topics.

Spark Structured Streaming consumes these topics, validates and cleans the data, and writes raw events into a Bronze layer.

Silver processing removes duplicates, handles null values, and standardises records.

Gold processing calculates:

- Live sales
- Popular products
- Inventory alerts
- Customer behaviour metrics

Separate consumer groups can simultaneously:

- Send notifications
- Detect fraud
- Update inventory
- Load the data warehouse
- Store data in a data lake

---

# 15. Final Data-Engineering Flow

```text
Data generated continuously
           │
           ▼
Producer publishes events
           │
           ▼
Kafka stores events in topics and partitions
           │
           ▼
Consumer groups read independently
           │
           ▼
Spark cleans, transforms and aggregates
           │
           ▼
Bronze → Silver → Gold
           │
           ▼
Dashboard, alerts, warehouse and ML systems
```

---

# 16. Main Takeaway

**Kafka is the transport and event backbone of a modern data platform.**

It helps data engineers:

- Collect data from many systems
- Transport events reliably
- Buffer sudden data volume
- Distribute events to multiple consumers
- Process information in real time
- Replay data when required
- Build scalable Bronze, Silver, and Gold pipelines
