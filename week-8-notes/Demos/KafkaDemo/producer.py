from  __future__ import annotations
import json
import time
from typing import Any
from confluent_kafka import Producer,Message


BOOTSTRAP_SERVERS = 'localhost:9092'
TOPIC="food-orders-new"

def delivery_report(error: Any, message: Message) -> None:
    if error is not None:
        print(f"FAILED :{error}")
        return
    
    key=message.key().decode('utf-8') if message.key() else None
    print(
        "DELIVERED"
        f" | TOPIC: {message.topic()}"
        f" | PARTITION: {message.partition()}"
        f" | KEY: {key}"
        f"| OFFSET: {message.offset()}"
    )
    
def main() -> None:
    producer = Producer(
        {"bootstrap.servers": BOOTSTRAP_SERVERS,
         "client.id": "food-orders-producer",
         }
    )
    
    orders=[
        {
            "order_id": "ORD-1001",
            "restaurant_id": "REST-01",
            "customer_name": "John Doe",
            "item": "Pizza",
            "quantity": 2,
            "price": 19.99,
            "status": "PLACED"
            
        },
        {
            "order_id": "ORD-1002",
            "restaurant_id": "REST-02",
            "customer_name": "Jane Smith",
            "item": "Burger",
            "quantity": 1,
            "price": 9.99,
            "status": "PLACED"
        },
        {
            "order_id": "ORD-1003",
            "restaurant_id": "REST-03",
            "customer_name": "Alice Johnson",
            "item": "Pasta",
            "quantity": 3,
            "price": 14.99,
            "status": "PLACED"  
        },
        {
            "order_id": "ORD-1004",
            "restaurant_id": "REST-04",
            "customer_name": "Bob Brown",
            "item": "Salad",
            "quantity": 1,
            "price": 7.99,
            "status": "PLACED"
        }
    ]
    
    print(f"Broker: {BOOTSTRAP_SERVERS} | Topic: {TOPIC}")
    print(f"Sending{len(orders)} events to Kafka...")
    
    for order in orders:
        producer.produce(
            topic=TOPIC,
            key=order["restaurant_id"],
            value  =json.dumps(order),
            callback=delivery_report
        )
        producer.poll(0)
        
        print(f"SENT: {order['order_id']}- {order['item']}")
        time.sleep(2)
        
        message_remaining=producer.flush(timeout=10)
        
        if message_remaining:
            raise   RuntimeError(f"{message_remaining} message(s) were not delivered before timeout.")
        
        print("\n Producer completed Sucessfully.")
        
if __name__ == "__main__":
    main()