

# Reliable API service

The idea is to demonstrate a service used to wrap around an unreliable external service.

## Design

The core design is a single threaded event loop to manage the concurrency. We use a lock/mutex around connection to the external service to synchronise external network calls and to avoid going over 10 times per minute. We start a long running task on startup which checks the queue at regular intervals.

### Justification

While I considered a separate thread to manage calls to the external service. With only a single call every 6 seconds it felt like the outstanding event loop in the thread could easily handle it. If the design constraint of requests per minute to the external service is higher we might change this approach. 

I had already opted for Python as my strongest language, and due to the GIL we wouldn't achieve true parallelism with multiple threads anyway.  Network requests should release the GIL. But using an event loop with a single thread puts the developer in control of managing the concurrency.

If I had gone for a none ASGI application and just a WSGI. Using a separate thread to manage connection to the external service could work. We'd need to manage synchronisation to the service in a thread-safe way however. If we went with the multiple thread approach we'd have to manage connection to the external service with a thread safe lock. But this would be a reasonable approach.

Multiple processes would likely be overkill for this. We'd have to think about sharing state between the processes given they don't share memory. The tasks are network requests ie IO bound not CPU bound so I believe this would be the wrong approach.

The main negative of the event loop approach in Python is all the code has to be written async, and any missing awaits can block the event loop and block the server. Testing can be painful.


## Other/future things

- Authorisation of the webhook.
- Just throwing messages away after a number of attempts - we'd want these to be saved either to a dead letter queue or permanent storage such as a database.
- Use RabbitMQ for the persistent queue. Decided it currently wasn't worth the effort for this demonstration. It would take care of the dead letter element.
- We've not really thought about security of messages held in the queue. With RSA we're only trying to ensure we can verify the messages have been authorised by some authority. The contents aren't necessarily sensitive. If the contents are sensitive RabbitMQ can be configured with TLS. We can also encrypt the data in the application layer with symmetric encryption.


## Local dev

### Setup
- Install `poetry` following their [instructions](https://python-poetry.org/docs/#installation).

- Install Python environment manager of your choice, and create Python=3.11 environment eg.
```sh
conda create --name reliable-api-service python=3.11
conda activate reliable-api-service
poetry install
```

### Add a dependency 
There's 2 ways:
1. `poetry add foo`
2. Add package and version manually to `pyproject.toml` and run `poetry update`.


### Running in dev mode
After migrating your DB to the latest. Run postgres in one terminal with
```
docker-compose up db
```
In another terminal, run the dev server with
```
fastapi dev app/main.py
```

### API Docs
To view the docs head to
```
http://localhost:8000/docs
```
Once the app is running.


## Production
If you just want to build the container
```
docker build . --tag fastapi_crud_app-web
```
If you want to build and run all the services together, we're using docker-compose to serve our app.
```
docker-compose up --build
```
