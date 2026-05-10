# Event Memory Experiment

This folder contains the experiment code only. Generated artifacts are grouped below:

```text
results/
  legacy/      Baseline, expanded, Pilot v2 event/MU retrieval CSVs
  ablation/    Pilot v2/v3 ablation CSVs

reports/
  legacy/      Early baseline, Pilot v2, QCA, and MU-level reports
  ablation/    Pilot v2/v3 ablation reports
```

Core scripts:

```text
run_experiment.py             Event-level retrieval experiment
run_memory_experiment.py      MU-level retrieval experiment
run_ablation_experiment.py    MU-level ablation experiment
generate_ablation_report.py   Markdown report generator for ablation CSVs
```

Recommended current artifacts:

```text
results/ablation/results_pilot_v3_ablation_memory_topk.csv
reports/ablation/evaluation_report_pilot_v3_ablation_zh.md
```

Example commands:

```powershell
py run_ablation_experiment.py --input E:\MyDatum\小论文\Codex\data\pilot_v3_dataset.jsonl --output results\ablation\results_pilot_v3_ablation_memory_topk.csv --top-k-values 5,10
py generate_ablation_report.py --input results\ablation\results_pilot_v3_ablation_memory_topk.csv --output reports\ablation\evaluation_report_pilot_v3_ablation_zh.md
```
