# Benchmarks reported by SenseNova

The table below transcribes the chart in the official **SenseNova-Loop-9B-Preview** model card. These are the model authors' reported scores for the original checkpoint and comparison models. They are not independent measurements, Q8_0 results, LM Studio throughput numbers, or benchmark results produced by this recipe.

Source: [official model card](https://huggingface.co/sensenova/SenseNova-Loop-9B-Preview/blob/27abea779b1e6634b136805b6519371739d551f7/README.md), revision `27abea779b1e6634b136805b6519371739d551f7`, checked on 2026-10-30. The chart is attributed to SenseNova / OpenSenseNova; the original model repository is Apache-2.0 licensed.

## Complete comparison

Values and model names follow the source chart. No percent signs or metric definitions have been added where the chart does not specify them. Column order is consistent across rows; the source figure sorts comparison models separately in each panel.

| Benchmark | SenseNova-Loop-9B-Preview | Nanbeige 4.2-3B | IQuest-Coder-V1-40B-Loop Thinking | Qwen3.5 9B | Qwen3.5 35B-A3B | Qwen3.6 35B-A3B | Qwen3.5 27B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BIRD-Dev | 71.38 | 46.35 | 54.80 | 68.48 | 69.34 | 69.80 | 69.84 |
| WorkBuddy Bench | 66.89 | 39.59 | 22.73 | 41.63 | 54.44 | 61.98 | 60.53 |
| AIDABench | 58.87 | 43.69 | 30.26 | 40.78 | 42.40 | 54.24 | 57.19 |
| TeamBench | 48.89 | 14.44 | 6.67 | 33.33 | 37.78 | 44.44 | 44.44 |
| Terminal Bench 2.1 | 40.45 | 49.44 | 17.98 | 29.20 | 40.45 | 40.45 | 47.19 |
| T³-Banking | 18.56 | 6.19 | 12.19 | 9.47 | 10.31 | 13.54 | 19.59 |
| AutomationBench | 13.72 | 2.77 | 5.29 | 1.05 | 2.67 | 9.33 | 10.17 |
| RaccoonPPTBench | 70.70 | Not shown | 22.56 | 33.60 | 53.80 | 64.30 | 59.08 |

The chart does not show a Nanbeige score for RaccoonPPTBench. Its footnote identifies RaccoonPPTBench as an internally developed presentation-generation benchmark covering content organization, visual presentation, and finished-output quality. The source card's technical report was marked TBD at the revision above. It does not provide a complete evaluation protocol alongside this figure, so identical prompts, tool environments, sampling settings, and runtime conditions cannot be inferred from these scores.

## Original figure

![Official SenseNova benchmark comparison across eight tasks](https://huggingface.co/sensenova/SenseNova-Loop-9B-Preview/resolve/27abea779b1e6634b136805b6519371739d551f7/assets/loop9b-benchmark-results.png)

[Open the full-resolution chart](https://huggingface.co/sensenova/SenseNova-Loop-9B-Preview/resolve/27abea779b1e6634b136805b6519371739d551f7/assets/loop9b-benchmark-results.png). The image is linked to its original host and pinned revision.

## What was tested for this recipe

Our [validation records](validation/) cover reference next-token comparisons, a few LM Studio text-generation smoke tests, and CPU regression comparisons for a separate upstream candidate. They do not establish that the quantized export reproduces the published task scores. This recipe supports text input; it does not enable the original model's image input or MTP features.
