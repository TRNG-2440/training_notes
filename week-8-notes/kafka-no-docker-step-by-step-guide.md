# Kafka Streaming on Windows Without Docker

## Goal

Run one local Apache Kafka broker in KRaft mode and use Python programs to
publish and consume food-order events.

## Architecture

```text
producer.py
    |
    | sends JSON events to localhost:9092
    v
Kafka broker
    |
    +-- Topic: food-orders
          +-- Partition 0
          +-- Partition 1
          +-- Partition 2
    |
    | consumer subscribes and polls
    v
consumer.py
```

`localhost:9092` is a Kafka TCP network address. It is not a website and it
does not provide a browser page.

---

# Part 1 — What you need

Install:

1. Java 17 or newer
2. Apache Kafka binary distribution
3. Python
4. Visual Studio Code
5. VS Code Python extension

Recommended Kafka extraction path:

```text
C:\kafka43
```

Keep the path short because Windows batch commands can fail when Kafka is
placed inside a deeply nested folder.

Verify:

```powershell
java -version
py --version
code --version
```

---

# Part 2 — First-time Kafka setup

Open one VS Code window. You do not need two VS Code windows.

## Step 1: Open the Kafka folder

```powershell
cd C:\kafka43
code .
```

## Step 2: Generate a cluster ID

Run:

```powershell
.\bin\windows\kafka-storage.bat random-uuid
```

Copy the final ID printed by the command. For example:

```text
Ycqt064WSGqOrN-uoxVAKQ
```

A logging warning may appear before the ID on Windows. The cluster ID is the
long final value containing letters, numbers, hyphens or underscores.

## Step 3: Format Kafka storage

Replace the example ID with your own:

```powershell
.\bin\windows\kafka-storage.bat format --standalone -t Ycqt064WSGqOrN-uoxVAKQ -c .\config\server.properties
```

Run this format step only once for a fresh Kafka data directory.

## Step 4: Start the broker

```powershell
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

Keep this terminal open. Closing it stops Kafka.

---

# Part 3 — One VS Code window and terminal layout

One VS Code window is enough. Use three integrated terminals:

| Terminal | Purpose | Must remain running? |
|---|---|---|
| Terminal 1 | Kafka broker | Yes |
| Terminal 2 | Create topic, then run consumer | Consumer must remain running |
| Terminal 3 | Run producer | No; it exits after sending |

For a classroom demonstration, a fourth terminal can be used only for Kafka
administration commands. It is optional.

---

# Part 4 — Verify port 9092

Open another VS Code terminal:

```powershell
Test-NetConnection -ComputerName localhost -Port 9092
```

Expected:

```text
TcpTestSucceeded : True
```

You can also run:

```powershell
netstat -ano | findstr :9092
```

The strongest verification is to ask Kafka itself:

```powershell
cd C:\kafka43

.\bin\windows\kafka-topics.bat --bootstrap-server localhost:9092 --list
```

Do not open `http://localhost:9092` in a browser. Port 9092 uses Kafka's
network protocol, not HTTP.

---

# Part 5 — Create the topic

With the broker running, use Terminal 2:

```powershell
cd C:\kafka43

.\bin\windows\kafka-topics.bat --create --if-not-exists --topic food-orders --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

Describe it:

```powershell
.\bin\windows\kafka-topics.bat --describe --topic food-orders --bootstrap-server localhost:9092
```

The topic has three partitions. Replication factor is one because this local
exercise uses one broker.

---

# Part 6 — Create the Python project

Create this folder:

```text
C:\kafka-python-demo
```

Open it:

```powershell
mkdir C:\kafka-python-demo
cd C:\kafka-python-demo
code .
```

Create these files in this order:

```text
kafka-python-demo/
├── requirements.txt
├── producer.py
├── consumer.py
└── .gitignore
```

## File 1: requirements.txt

```text
confluent-kafka==2.15.0
```

This tells pip which Kafka client library to install.

## File 2: producer.py

`producer.py` is included in this project. It:

1. connects to `localhost:9092`;
2. creates five Python dictionaries;
3. converts each dictionary to JSON;
4. sends each event to `food-orders`;
5. uses `restaurant_id` as the message key;
6. prints partition and offset after Kafka acknowledges the event;
7. waits until all messages are delivered.

## File 3: consumer.py

`consumer.py` is included in this project. It:

1. connects to `localhost:9092`;
2. joins the `food-order-analytics-group`;
3. subscribes to `food-orders`;
4. asks Kafka for messages with `poll()`;
5. converts JSON back to a Python dictionary;
6. displays topic metadata;
7. stops after five events;
8. closes safely.

---

# Part 7 — Create the Python environment

Inside the project folder:

```powershell
py -m venv .venv
```

Activate it:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify:

```powershell
python -c "import confluent_kafka; print(confluent_kafka.version())"
```

In VS Code select:

```text
Ctrl+Shift+P
Python: Select Interpreter
.venv
```

Do not copy a `.venv` from another computer. Recreate it locally.

---

# Part 8 — Correct execution order

Every time you demonstrate the application:

## Terminal 1 — Start Kafka

```powershell
cd C:\kafka43
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

## Terminal 2 — Verify the topic

```powershell
cd C:\kafka43
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092
```

If `food-orders` is missing, create it.

## Terminal 2 — Start the consumer first

```powershell
cd C:\kafka-python-demo
.\.venv\Scripts\Activate.ps1
python consumer.py
```

It waits for events.

## Terminal 3 — Start the producer second

```powershell
cd C:\kafka-python-demo
.\.venv\Scripts\Activate.ps1
python producer.py
```

The producer sends five events. The consumer receives them immediately.

---

# Part 9 — Producer code explanation

## Imports

```python
import json
import time
from confluent_kafka import Message, Producer
```

- `json` converts Python dictionaries into JSON text.
- `time` creates a one-second delay between events.
- `Producer` connects and sends events to Kafka.
- `Message` is used as a type in the delivery callback.

## Connection settings

```python
BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "food-orders"
```

- `localhost` means Kafka is running on this computer.
- `9092` is the broker's client port.
- `food-orders` is the target topic.

## Delivery callback

```python
def delivery_report(error, message):
```

Kafka calls this function asynchronously after an event succeeds or fails.

On success, it displays:

- topic;
- partition;
- offset;
- message key.

## Producer object

```python
producer = Producer(
    {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "client.id": "food-order-producer",
    }
)
```

`bootstrap.servers` gives the initial broker address. The producer obtains
cluster and topic metadata after connecting.

## Event data

```python
orders = [
    {
        "order_id": "ORD-1001",
        ...
    }
]
```

Each dictionary represents one business event.

## Produce

```python
producer.produce(
    topic=TOPIC,
    key=order["restaurant_id"],
    value=json.dumps(order),
    callback=delivery_report,
)
```

- `topic` selects the stream.
- `key` helps Kafka route related restaurant events consistently.
- `value` is the JSON event payload.
- `callback` reports delivery success or failure.

## Poll

```python
producer.poll(0)
```

This lets the client execute pending delivery callbacks without waiting.

## Sleep

```python
time.sleep(1)
```

This is not required by Kafka. It is included only to make streaming visible:
one event appears every second.

## Flush

```python
producer.flush(timeout=10)
```

Kafka sends asynchronously. `flush()` waits for queued messages before Python
exits.

---

# Part 10 — Consumer code explanation

## Consumer group settings

```python
GROUP_ID = os.getenv(
    "KAFKA_GROUP_ID",
    "food-order-analytics-group",
)
```

A consumer group identifies one logical consuming application. Kafka stores
the group's progress as offsets.

## Consumer object

```python
consumer = Consumer(
    {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }
)
```

- `bootstrap.servers`: Kafka connection address.
- `group.id`: identifies the consumer application.
- `auto.offset.reset=earliest`: when the group has no valid stored offset,
  begin at the oldest available event.
- `enable.auto.commit=True`: periodically store the group's progress.

`earliest` does not force old events to be replayed every time. It applies
only when the group has no valid committed offset.

## Subscribe

```python
consumer.subscribe([TOPIC])
```

Registers interest in the `food-orders` topic.

## Poll

```python
message = consumer.poll(timeout=1.0)
```

The consumer waits for up to one second for an event. `None` means no event
arrived during that poll.

## Decode the event

```python
order = json.loads(message.value().decode("utf-8"))
```

1. Kafka returns bytes.
2. `decode("utf-8")` converts bytes into text.
3. `json.loads()` converts JSON text into a Python dictionary.

## Metadata

```python
message.partition()
message.offset()
message.key()
```

This shows where Kafka stored the event.

## Close

```python
consumer.close()
```

Leaves the consumer group and releases network resources.

---

# Part 11 — Complete runtime flow

```text
1. Kafka broker starts
       |
       v
2. Broker listens on localhost:9092
       |
       v
3. food-orders topic exists with 3 partitions
       |
       v
4. consumer.py connects and subscribes
       |
       v
5. producer.py connects
       |
       v
6. producer converts an order dictionary to JSON
       |
       v
7. producer sends topic + key + value
       |
       v
8. broker chooses a partition and appends the event
       |
       v
9. broker assigns the next offset in that partition
       |
       v
10. consumer polls and receives the event
       |
       v
11. consumer decodes JSON and prints the order
       |
       v
12. consumer group records its progress
```

---

# Part 12 — Verify data and the consumer group

Read events using Kafka's console consumer:

```powershell
cd C:\kafka43

.\bin\windows\kafka-console-consumer.bat --topic food-orders --from-beginning --bootstrap-server localhost:9092 --property print.key=true --property print.partition=true --property print.offset=true
```

Press `Ctrl+C` to stop.

List consumer groups:

```powershell
.\bin\windows\kafka-consumer-groups.bat --bootstrap-server localhost:9092 --list
```

Describe the Python consumer group:

```powershell
.\bin\windows\kafka-consumer-groups.bat --bootstrap-server localhost:9092 --describe --group food-order-analytics-group
```

Important columns:

- `CURRENT-OFFSET`: next position the group will read;
- `LOG-END-OFFSET`: latest position in the partition;
- `LAG`: unread messages.

---

# Part 13 — Run the demo again

The existing group remembers its offsets. The easiest repeat demonstration is:

1. start `consumer.py`;
2. start `producer.py`;
3. consume the five newly generated events.

To replay using a new group:

```powershell
$env:KAFKA_GROUP_ID="food-order-reporting-group"
python consumer.py
```

To return to the default group in the current terminal:

```powershell
Remove-Item Env:KAFKA_GROUP_ID
```

---

# Part 14 — Stop the applications

Stop producer or consumer:

```text
Ctrl+C
```

Stop Kafka from its broker terminal:

```text
Ctrl+C
```

When restarting later, do not format storage again. Start the broker directly.

---

# Part 15 — Troubleshooting checklist

## Broker will not start

Check Java:

```powershell
java -version
```

Check whether port 9092 is already used:

```powershell
netstat -ano | findstr :9092
```

## Topic command cannot connect

Confirm the broker terminal is still running:

```powershell
Test-NetConnection localhost -Port 9092
```

## Python import error

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Consumer shows nothing

Verify:

1. broker is running;
2. topic exists;
3. consumer is running;
4. producer was run after the consumer;
5. both Python files use exactly `localhost:9092`;
6. both use exactly `food-orders`.

## Consumer waits on a repeated run

The group may already have consumed all existing messages. Start the producer
to create new messages or use a new `KAFKA_GROUP_ID`.

## Browser shows nothing on 9092

That is expected. Kafka port 9092 is not an HTTP website.
