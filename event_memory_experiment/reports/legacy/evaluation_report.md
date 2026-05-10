# Toy Experiment Evaluation

## Setup

- Dataset: 5 synthetic users, 15 events, 60 memories, 20 queries.
- Methods: recency_only, similarity_only, recency_similarity_hybrid, proposed_TMT_decay_event_memory.
- Context size: top 3 events.

## Overall Results

| method | supporting_event_recall | top1_accuracy | top3_recall | NDCG@3 | LLM can answer | avg token cost |
|---|---:|---:|---:|---:|---:|---:|
| recency_only | 1.000 | 0.850 | 1.000 | 0.914 | 1.000 | 295.2 |
| similarity_only | 1.000 | 0.850 | 1.000 | 0.923 | 1.000 | 295.2 |
| recency_similarity_hybrid | 1.000 | 0.850 | 1.000 | 0.914 | 1.000 | 295.2 |
| proposed_TMT_decay_event_memory | 1.000 | 0.850 | 1.000 | 0.908 | 1.000 | 295.2 |

## More Diagnostic Derived Results

Because each user has only 3 events and the experiment selects top 3 events, top3 recall and LLM-can-answer are saturated. A more diagnostic view is derived from the same ranking by looking at top1 and top2.

| method | recall@1 | recall@2 | all gold events in top2 | NDCG@3 |
|---|---:|---:|---:|---:|
| recency_only | 0.492 | 0.833 | 0.700 | 0.914 |
| similarity_only | 0.492 | 0.833 | 0.700 | 0.923 |
| recency_similarity_hybrid | 0.492 | 0.833 | 0.700 | 0.914 |
| proposed_TMT_decay_event_memory | 0.492 | 0.808 | 0.700 | 0.908 |

By query mode:

| group | recall@2 | top1_accuracy | NDCG@3 |
|---|---:|---:|---:|
| recency_only, task | 0.950 | 0.800 | 0.920 |
| similarity_only, task | 0.900 | 0.800 | 0.914 |
| recency_similarity_hybrid, task | 0.950 | 0.800 | 0.920 |
| proposed_TMT_decay_event_memory, task | 0.750 | 0.800 | 0.894 |
| recency_only, chat | 0.717 | 0.900 | 0.908 |
| similarity_only, chat | 0.767 | 0.900 | 0.932 |
| recency_similarity_hybrid, chat | 0.717 | 0.900 | 0.908 |
| proposed_TMT_decay_event_memory, chat | 0.867 | 0.900 | 0.921 |

## Interpretation

The current toy experiment is useful as a pipeline sanity check, but it is not yet a strong effectiveness experiment. Since every user has exactly 3 events and top_k is also 3, every method eventually places all events into context. This makes supporting_event_recall, top3_recall, LLM-can-answer, and token_cost uninformative.

The proposed method does not win overall on this toy set. It is slightly worse on task queries, mainly because the current TMT/event scoring can over-promote events containing overdue or near-deadline todo memories even when the query asks for a specific task domain or status. Examples include u003_q002 and u004_q001, where the gold event appears only at rank 3.

The proposed method shows a useful signal on chat/mixed queries: recall@2 is higher than the baselines. This matches the design goal that mixed or chat queries should preserve preference, habit, and fact memories instead of only the newest or semantically closest task event.

Similarity-only currently performs surprisingly well because the dataset is small and event themes are cleanly separated. However, the query text is Chinese while most memory/event content is English, so the current lexical similarity scorer is not a real semantic model. This result should not be interpreted as evidence that lexical similarity is enough.

## Conclusion

This run validates that the modules can load data, rank events, compute metrics, and export CSV. It does not yet validate the research hypothesis.

To make the experiment meaningful, the next dataset should contain more distractor events per user, ideally 6-10 events, and context should be limited to top1 or top2 for diagnosis. The proposed method also needs a stronger query-mode router for task_status and task_domain constraints, so deadline activation does not override explicit query intent.

