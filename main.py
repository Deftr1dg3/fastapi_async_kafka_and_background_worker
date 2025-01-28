from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
import json

from pydantic import BaseModel, Field, ValidationError, EmailStr, ConfigDict
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from uuid6 import uuid7

REQUEST_TOPIC = "request_topic"
RESPONSE_TOPIC = "response_topic"
BOOTSTRAP_SERVERS = "localhost:9092"
GROUP_ID = "fastapi-group"



# -----------------------------------------------------------------------------
# Presetting Kafka Producer and Consumer
# -----------------------------------------------------------------------------

# In-memory store of correlation_id -> Future
pending_requests = {}



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: create producer, consumer; start background task.
    Shutdown: stop background task, close consumer & producer.
    """
    
    # Actions that will be performed on Startup ---------------------
    
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    await producer.start()

    consumer = AIOKafkaConsumer(
        RESPONSE_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID
    )
    await consumer.start()

    # Background task for handling responses from response_topic
    task = asyncio.create_task(consume_responses(consumer))

    # Attach to app.state so we can use them in routes
    app.state.producer = producer
    app.state.consumer = consumer
    app.state.consume_task = task

    try:
        # Returns controll to the FastAPI app.
        # Actually enables endpoint.
        yield
    finally:
        # Actions that will be performed on Shutdown ---------------------
        # Get controll back from FastAPI app
        # once the app execution has been terminated by Ctrl+C
        # Closes all services
        task.cancel()
        await consumer.stop()
        await producer.stop()

async def consume_responses(consumer: AIOKafkaConsumer):
    """Consumes messages from response_topic; resolves the pending_requests futures."""
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode("utf-8"))
            correlation_id = data.get("correlation_id")
            result = data.get("result")

            future = pending_requests.pop(correlation_id, None)
            if future and not future.done():
                future.set_result(result)

    except asyncio.CancelledError:
        # task cancelled during shutdown
        pass
    except Exception as e:
        print(f"[consume_responses] Error: {e}")


# -----------------------------------------------------------------------------
# Pydentic model 
# -----------------------------------------------------------------------------

class InputSchema(BaseModel):
    input: str
    
    # This specific configuration specifies that the 
    # model should reject any extra fields that are 
    # not explicitly defined in the model schema.
    model_config = ConfigDict(extra='forbid')
    

# -----------------------------------------------------------------------------
# APP Code 
# -----------------------------------------------------------------------------

app = FastAPI(lifespan=lifespan)

@app.post("/process")
async def process_request(payload: InputSchema):
    """
    1) Generate correlation_id
    2) Create a Future and store it
    3) Send to Kafka request_topic
    4) Await the Future
    5) Return result
    """ 
    correlation_id = str(uuid7())
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    pending_requests[correlation_id] = future

    message = {
        "correlation_id": correlation_id,
        "input": payload.input
    }

    # Send the request to the request_topic
    await app.state.producer.send_and_wait(
        REQUEST_TOPIC,
        json.dumps(message).encode("utf-8")
    )

    # Wait for the worker's response
    result = await future

    return {
        "message": "Request processed successfully",
        "result": result
    }


# To run app use 'uvicorn' server 
#  uvicorn main:app --host 0.0.0.0 --port 8000 

#  Access UI 'localhost:8000/docs'