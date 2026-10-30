# Source and validation notes

## Two source tracks

| Track | Base commit | Patches | Evidence |
| --- | --- | --- | --- |
| LM Studio reproduction | `ff0d396e3dda0f33e7ce5ad4267fce4f7690cfb1` | `patches/lmstudio/01-clover-pr31306.patch`, then `02-sensenova-loop-native.patch` | Native GPU and LM Studio text smoke tests on the pinned runtime |
| Upstream candidate | `a34de8618b25dfc32ee43749db47d767a9f0a25d` | `patches/upstream/sensenova-loop-upstream.patch` only | CPU build, 68 CTest tests, architecture and regression checks |

These patches are alternatives on different bases. Do not apply them together or install the newer upstream candidate into LM Studio using the legacy staging recipe. Its binary compatibility with LM Studio has not been validated.

The LM Studio track reproduces the already-working integration. The upstream candidate removes the Clover prerequisite and adds fixes for preserving loop metadata on model save, loop-count overflow validation, and final-layer output cropping when a loop ends at the last layer. Those fixes have **not** been backported or validated in the LM Studio track. The published GGUF uses the tested fixed loop schedule and has suffix layers after the loop. Do not generalize the legacy track to arbitrary loop metadata or model save/re-export workflows.

## Native execution

The model's physical layer schedule is `[0..3] + [4..27] * 2 + [28..31]`. The converter expands that into 56 GGUF block entries. Repeated weights are stored twice so each virtual visit receives its own attention and recurrent cache state. This increases the model file size; it is not fine-tuning or new learned parameters.

The native graph reuses Qwen3.5 attention and feed-forward operations. Within repeated blocks, learned FP32 mHC routers read from and update two residual streams, using sigmoid gates and Sinkhorn normalization. The streams are averaged at loop-pass boundaries. Routing tensors and required loop metadata are model-specific.

The new architecture is named `sensenova_loop`; changing a GGUF architecture string to `qwen35` cannot reproduce this computation.

## Build the separate upstream candidate on CPU

```bash
git clone https://github.com/ggml-org/llama.cpp.git .work/llama.cpp-upstream
git -C .work/llama.cpp-upstream checkout a34de8618b25dfc32ee43749db47d767a9f0a25d
git -C .work/llama.cpp-upstream apply "$PWD/patches/upstream/sensenova-loop-upstream.patch"
cmake -S .work/llama.cpp-upstream -B .work/llama.cpp-upstream/build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=OFF -DGGML_NATIVE=OFF -DLLAMA_BUILD_TESTS=ON
cmake --build .work/llama.cpp-upstream/build --parallel 8
.work/llama.cpp-upstream/build/bin/test-llama-archs \
  -a 'sensenova_loop|qwen35$' -b CPU
```

The full CTest suite additionally uses Python dependencies and downloads test fixtures. Install its requirements as documented in the pinned checkout. Git LFS is needed for the external tokenizer vocabulary fixture repository; pointer files are not valid GGUF files.

```bash
ctest --test-dir .work/llama.cpp-upstream/build --output-on-failure -j4
```

## Recorded validation

The LM Studio track's BF16 and Q8 native logits were checked against the official model implementation on three short prompts. All matched the reference top-1 token. LM Studio also answered a multiplication question, wrote a Python square function, and recalled a conversation codename. These are smoke tests, not general benchmark scores.

For the separate upstream candidate:

- 68 distinct CPU CTest tests passed. The first run passed 67; the tokenizer fixture test passed after actual Git LFS data replaced pointer files.
- 48 paired comparisons against the unmodified base were bit-for-bit identical: LFM3 dense, Llama dense/MoE, Qwen3.5 dense/MoE, and Qwen3-Next MoE. These used small synthetic fixtures, four prompt lengths, nine decode steps per case, and FP16/Q8 KV caches: 55,296 logits total.
- SenseNova and Qwen3.5 inference, save/reload, and mixed-batch checks passed. SenseNova checks reject eight invalid metadata cases and six missing keys, and exercise two valid loop boundaries.
- The real Q8 checkpoint was also compared against official reference logits with default and Q8 KV caches on CPU.

These results do not establish full-checkpoint equivalence for the other models or coverage across CUDA, Metal, and Vulkan. The newer candidate has not passed a full cross-platform CI matrix or full-model perplexity benchmark. Validation files distinguish the two tracks.

## Provenance

- Model: `sensenova/SenseNova-Loop-9B-Preview`, revision `27abea779b1e6634b136805b6519371739d551f7`.
- Published GGUF: `notfakerv/SenseNova-Loop-9B-Preview-GGUF`, revision `b54ee83643a4e8066290d3062e1a218139c4c007`.
- Clover prerequisite: Maphist0, PR #31306, revision `4838ffb0c8ade92f34d9157deea38d92758ab824`.
- Native SenseNova adaptation, packaging, scripts, and validation: notfakerv / GitHub renoirvieir4, with substantial OpenAI Codex assistance.

This is a personal reproduction repository, not a submission to ggml-org/llama.cpp. Any upstream contribution must follow that project's current contribution and disclosure policies.
