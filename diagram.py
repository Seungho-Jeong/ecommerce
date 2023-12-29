from diagrams import Cluster, Diagram, Edge
from diagrams.elastic.elasticsearch import Elasticsearch
from diagrams.onprem.ci import Jenkins
from diagrams.onprem.client import Client, Users
from diagrams.onprem.compute import Server
from diagrams.onprem.database import Postgresql
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.monitoring import Grafana, Prometheus, Sentry
from diagrams.onprem.network import Envoy, Gunicorn
from diagrams.onprem.queue import Celery, Rabbitmq
from diagrams.onprem.registry import Harbor
from diagrams.onprem.tracing import Jaeger
from diagrams.onprem.vcs import Github
from diagrams.programming.framework import Django

with Diagram("", show=False, filename="architecture"):
    users = Users("users")

    ide = Client("VSCode")
    github = Github("GitHub")
    jenkins = Jenkins("Jenkins")
    harbor = Harbor("Harbor")

    with Cluster("Service Cluster"):
        envoy = Envoy("Envoy")
        with Cluster("API Containers"):
            django2 = Django("API 1")
            django = Django("API 2")
            django3 = Django("others...")

        celery_worker = Celery("Worker Container")
        rabbitmq = Rabbitmq("RabbitMQ")
        rabbitmq_consumer = Server("Consumer Container")

        with Cluster("Redis HA Containers"):
            redis = Redis("primary")
            redis_replica = Redis("replica")

        sentry = Sentry("Sentry")
        es = Elasticsearch("ElasticSearch")
        jaeger = Jaeger("Jaeger")

    prometheus = Prometheus("Prometheus")
    grafana = Grafana("Grafana")

    with Cluster("AWS Aurora RDS"):
        postgres = Postgresql("primary")
        postgres_readonly = Postgresql("readonly")

    users >> envoy >> django
    django3 >> postgres - postgres_readonly
    django2 >> redis - redis_replica >> celery_worker
    django2 >> rabbitmq >> rabbitmq_consumer
    django >> es
    django2 >> sentry
    django3 >> jaeger
    (
        [
            django3,
            postgres_readonly,
            redis_replica,
            rabbitmq,
            celery_worker,
            rabbitmq_consumer,
        ]
        << Edge(label="Collect")
        << prometheus
        << grafana
    )
    (
        ide
        >> Edge(label="push")
        >> github
        >> Edge(label="Webhook")
        >> jenkins
        >> Edge(label="Test & Build")
        >> harbor
        >> django3
    )
