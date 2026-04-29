import random

from locust import HttpUser, between, task


class ShortistUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.short_ids: list[str] = []

    @task(1)
    def shorten_link(self):
        response = self.client.post(
            "/links/shorten",
            json={
                "original_url": f"https://example.com/page-{random.randint(1, 1_000_000)}",
                "expire_at": "2030-01-01T00:00:00+00:00",
            },
            name="/links/shorten",
        )
        if response.status_code == 200:
            short_id = response.json().get("short_id")
            if short_id:
                self.short_ids.append(short_id)

    @task(3)
    def follow_link(self):
        if not self.short_ids:
            return
        short_id = random.choice(self.short_ids)
        self.client.get(
            f"/links/{short_id}",
            name="/links/[short_id]",
            allow_redirects=False,
        )
