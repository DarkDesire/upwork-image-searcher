# Upwork Image Searcher

Python 3.9.5. FastAPI + Celery + Redis + Selenium

This project won't start by default without **service_account.json** (credentials).

## Want to use this project?

Spin up the containers:

```sh
$ docker-compose up -d --build
```

Open your browser to [http://localhost:8004](http://localhost:8004) to view the app or to [http://localhost:5556](http://localhost:5556) to view the Flower dashboard.

Trigger a new task:

```sh
$ curl http://localhost:8004/tasks -H "Content-Type: application/json" --data '{"link": "url", "language":"eu", "country":"us"}'
```

Check the status:

```sh
$ curl http://localhost:8004/tasks/<TASK_ID>
```
