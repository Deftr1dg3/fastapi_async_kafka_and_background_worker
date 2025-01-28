# Simple FastAPI endpoint with async Kafka message broker and

# background worker.

### Run docker compose

    docker compose up -d

    To stop process run:

    docker compose down

### To run the app use

    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

    '--reload' == developers mode

### Run 'background_task.py'

    python ./background_task.py

### Access the FastAPI interface on

    localhost:8000/docs

## CLIs

Access bash in Kafka container

    docker exec -it <container_id> bash

1. Listing Topics
   kafka-topics --list --bootstrap-server localhost:9092

2. Getting Topic Details
   kafka-topics --describe \
    --topic <TOPIC_NAME> \
    --bootstrap-server localhost:9092

3. Use producer and consumer from shell

Using Console Consumer
kafka-console-consumer --bootstrap-server localhost:9092 \
 --topic <TOPIC_NAME> \
 --from-beginning

Using Console Producer
kafka-console-producer --broker-list localhost:9092 \
 --topic <TOPIC_NAME>

4. Create Kafka topic (Used for production to avoit Auto topic creation)
   kafka-topics \
    --create \
    --topic my_production_topic \
    --partitions 3 \
    --replication-factor 3 \
    --bootstrap-server your-kafka-broker:9092

## Listeners security protocols

Kafka supports several listener security protocols besides PLAINTEXT://. The most common are:

    PLAINTEXT://

No authentication, no encryption (everything in the clear).

    SSL://

Uses TLS/SSL encryption.
No additional username/password authentication at this layer, but data in transit is encrypted and broker identity is verified via certificates.
SASL_PLAINTEXT://

Uses SASL (Simple Authentication and Security Layer) for authentication, but data is still sent in the clear (no encryption).
Typically combined with GSSAPI (Kerberos), SCRAM, PLAIN mechanisms, etc.
SASL_SSL://

Uses SASL for authentication and SSL/TLS for encryption.
This is often used in production to ensure both secure authentication and encrypted traffic.
SASL Mechanisms
Within SASL, you can choose different authentication mechanisms (e.g., PLAIN, GSSAPI for Kerberos, SCRAM-SHA-256/512, OAUTHBEARER). For instance:

SASL_SSL + SCRAM-SHA-512
SASL_PLAINTEXT + PLAIN
etc.

But at the listener protocol level, you primarily see these four: PLAINTEXT, SSL, SASL_PLAINTEXT, and SASL_SSL.

Configuration Example
In the Kafka broker configuration (e.g., server.properties or environment variables in Docker), you might see lines like:

ini

```ini
listeners=PLAINTEXT://0.0.0.0:9092,SSL://0.0.0.0:9093,SASL_SSL://0.0.0.0:9094
advertised.listeners=PLAINTEXT://your-broker.com:9092,SSL://your-broker.com:9093,SASL_SSL://your-broker.com:9094
listener.security.protocol.map=PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_SSL:SASL_SSL
```

If you’re enabling SASL, you also need to set the appropriate mechanisms and JAAS configurations.

### In Summary

PLAINTEXT: No security.
SSL: Encrypted transport, no additional authentication.
SASL_PLAINTEXT: Authentication without encryption.
SASL_SSL: Both authentication and encryption.
Choosing the right protocol depends on your security requirements. In production, SASL_SSL is often recommended to secure both the connection (TLS) and the authentication (SASL).
