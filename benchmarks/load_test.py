"""Load test for concurrent request handling using Locust."""

from locust import HttpUser, task, between


class AegisUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def verify_response(self):
        self.client.post("/v1/verify", json={
            "response_text": "Python is a programming language created by Guido van Rossum in 1991.",
            "context": "Python is a high-level programming language. It was created by Guido van Rossum and first released in 1991.",
            "prompt": "Tell me about Python",
            "domain": "general",
        })

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def get_stats(self):
        self.client.get("/v1/dashboard/stats")
