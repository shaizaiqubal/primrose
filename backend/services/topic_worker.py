"""Run one complete topic-clustering pass for the current corpus."""

from backend.services.topics import run_topic_pipeline


if __name__ == "__main__":
    run_topic_pipeline()
