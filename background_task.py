import asyncio
import json

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

REQUEST_TOPIC = "request_topic"
RESPONSE_TOPIC = "response_topic"
BOOTSTRAP_SERVERS = "localhost:9092"
GROUP_ID = "worker-group"


async def ai_logic_here(input: str) -> str:
    # AI process is running HERE 
    #  ...
    #  ...
    #  ...
    return f"PROCEEDED AI RESPONSE: {input}"


async def main():
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    await producer.start()

    consumer = AIOKafkaConsumer(
        REQUEST_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID
    )
    await consumer.start()

    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode("utf-8"))
            correlation_id = data["correlation_id"]
            payload = data.get("payload", {})
            
            # "Process" the input by appending " Proceeded"
            original_input = payload.get("input", "")
            
            # Place for AI logic
            processed_text = await ai_logic_here(original_input)

            # Produce the response to response_topic
            response = {
                "correlation_id": correlation_id,
                "result": processed_text
            }
            await producer.send_and_wait(
                RESPONSE_TOPIC,
                json.dumps(response).encode("utf-8")
            )

    except Exception as e:
        print(f"[worker] Error: {e}")
    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
