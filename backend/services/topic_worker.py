"""Run one complete topic-clustering pass for the current corpus."""

import argparse

from backend.services.embedding_queue import publish_topic_naming_job
from backend.services.topics import run_topic_pipeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_id", type=int)
    args = parser.parse_args()
    run_topic_pipeline(args.corpus_id)
    publish_topic_naming_job(args.corpus_id)
