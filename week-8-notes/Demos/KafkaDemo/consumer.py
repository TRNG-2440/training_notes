from __future__ import annotations
import json
import os
from confluent_kafka import Consumer, KafkaError, KafkaException

BOOTSTRAP_SERVERS = 'localhost:9092'
TOPIC="food-orders-new"

GROUP_ID=os.getenv("KAFKA_GROUP_ID", "food-orders-analytics-group")
MAX_MEESAGES=int(os.getenv("MAX_MESSAGES", "5"))

def main() ->None:
    consumer=Consumer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,            
        }
    )
    
    consumer.subscribe([TOPIC])
    received=0
    
    print(f"Broker: {BOOTSTRAP_SERVERS} | Topic: {TOPIC} |Consumer  Group: {GROUP_ID}")
    print(f"Waiting for {MAX_MEESAGES} messages...\n")
    
    try:
        while received<MAX_MEESAGES:
            message=consumer.poll(timeout=1.0)
            
            if message is None:
                continue
            
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                
                raise KafkaException(message.error())

            order=json.loads(message.value().decode("utf-8"))
            key=message.key().decode("utf-8") if message.key() else None
            received+=1
            
            print(
                f"RECEIVED {received}/{MAX_MEESAGES}"
                f"| partition: {message.partition()} "
                f"| KEY: {key} "
                f"| OFFSET: {message.offset()}"
            )
            
            print(
                f"ORDER:{order['order_id']}"
                f"| customer: {order['customer_name']}"
                f"| item: {order['item']}"
                f"| amount: ${order['price']:.2f}"
                f"| status: {order['status']}"
            )
    except KeyboardInterrupt:
        print("Consumer stopped  by the  user. ")

    finally:
        consumer.close()
        print("Consumer closed.")

if __name__=="__main__":
    main()