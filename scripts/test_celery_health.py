from agentflow.workers.tasks import health_check


result = health_check.delay("Celery is working")

print(f"Task ID: {result.id}")
print(f"Result: {result.get(timeout=10)}")