from generation.helpers.questions import question_calls


def track_progress(progress: dict, chunk: dict, size: int) -> bool:
    """Update {"done", "total", "topics", "topics_ready"} from one graph stream chunk.

    `size` is the questions each topic gets. Returns True if it changed. The steps are the question calls; a topic is ready once all its
    calls finished. A retry replays steps that already finished, so counts are capped, and done
    stays below total until merging, which runs once every call has finished.
    """
    changed = False

    for node, update in chunk.items():
        if node == "human_review" and update["approved"]:
            subtopic_counts = [len(topic["subtopics"]) or 1 for topic in update["topics"]]
            topic_calls = [count * question_calls(count, size) for count in subtopic_counts]
            progress.update(
                done=0,
                total=sum(topic_calls),
                topics=len(topic_calls),
                topics_ready=0,
                topic_calls=topic_calls,
                topic_done=[0] * len(topic_calls),
            )
            changed = True
        elif node == "generate_questions":
            progress["done"] = min(progress["done"] + 1, progress["total"] - 1)

            # Progress saved before per-topic counts existed has none to update.
            if "topic_done" in progress:
                for entry in update["question_pool"]:
                    ti = entry["topic_index"]
                    progress["topic_done"][ti] = min(
                        progress["topic_done"][ti] + 1, progress["topic_calls"][ti]
                    )

                progress["topics_ready"] = sum(
                    done >= calls
                    for done, calls in zip(progress["topic_done"], progress["topic_calls"])
                )

            changed = True
        elif node == "merge_questions":
            progress["done"] = progress["total"]
            progress["topics_ready"] = progress.get("topics", 0)
            changed = True

    return changed
