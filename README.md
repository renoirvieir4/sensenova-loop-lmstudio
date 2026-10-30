# SenseNova Loop 9B in LM Studio

A source-based recipe for running **SenseNova-Loop-9B-Preview text chat natively in LM Studio** on Linux x86_64 with an NVIDIA GPU. It includes the GGUF download, pinned llama.cpp patches, build and runtime-staging scripts, API example, and rollback instructions.

**This is an unofficial, version-specific integration.** The working LM Studio route uses app **0.4.26+4**, stock **CUDA 12 AVX2 runtime 2.66.0**, and a locally built runtime named **2.66.101**. That custom version is not downloadable from LM Studio's runtime catalog. Do not substitute a newer llama.cpp library or another stock runtime without testing their binary compatibility.

The original model and architecture are by [SenseNova / OpenSenseNova](https://github.com/OpenSenseNova/SenseNova-Loop). The [Q8_0 GGUF](https://huggingface.co/notfakerv/SenseNova-Loop-9B-Preview-GGUF) was converted and validated by notfakerv with OpenAI Codex assistance. No fine-tuning was performed.

## What works

- Native text generation and conversation history in LM Studio.
- Loop execution: 32 physical layers become 56 virtual layer entries, with separate cache state for repeated visits.
- Two-stream manifold-constrained hyper-connections (mHC), with FP32 routing tensors.
- Q8_0 model weights, with convolution, normalization, and routing tensors retained in FP32.

This export does not implement image input, MTP, or diffusion acceleration. The tested context was **8,192 tokens**, with **one parallel prediction**. The original model's larger advertised context is not a validation claim for this integration.

## Before you begin

The recorded working machine used two RTX 3090 GPUs, CUDA toolkit 12.8, GCC 14, and Linux x86_64. Windows, macOS, AMD GPUs, and other LM Studio runtime versions are not covered by this recipe.

The GGUF occupies **15,069,056,512 bytes (14.03 GiB)**. Reserve at least 25 GiB of free disk for the model, source, and build, in addition to an existing CUDA toolkit. Runtime memory also includes cache and working buffers; the file size alone is not a VRAM requirement. The recorded run used both 24 GiB GPUs. Smaller configurations have not been validated here.

Install LM Studio and its `lms` CLI, then install build dependencies. On an apt-based Linux installation:

```bash
sudo apt-get update
sudo apt-get install git build-essential cmake ninja-build python3 python3-venv patchelf binutils
```

You also need Python 3.11 or newer and an NVIDIA CUDA toolkit with a compatible host compiler. The apt command above does not install CUDA or guarantee the tested GCC version. Confirm these before building:

```bash
python3 --version
cmake --version
nvcc --version
nvidia-smi
```

## 1. Get the recipe and stock runtime

Clone this repository, then enter its directory:

```bash
git clone https://github.com/renoirvieir4/sensenova-loop-lmstudio.git
cd sensenova-loop-lmstudio
export PATH="$HOME/.lmstudio/bin:$PATH"
lms runtime ls
lms runtime get llama.cpp-linux-x86_64-nvidia-cuda12-avx2@2.66.0
```

If 2.66.0 is already installed, skip the download. If it is unavailable in the catalog, stop this version-specific route; do not silently replace it with 2.67 or another version. The [official runtime documentation](https://lmstudio.ai/docs/cli/runtime/runtime) describes listing, downloading, and selecting runtimes.

Record your currently selected runtime from `lms runtime ls` so you can return to it. In LM Studio's runtime settings, turn off automatic runtime replacement/cleanup while using this custom runtime. Labels can differ by application version. Keep the original stock runtime installed.

## 2. Download and verify the model

```bash
python3 -m venv .venv
.venv/bin/python -m pip install 'huggingface_hub>=1.0,<2'
.venv/bin/python scripts/download_model.py
```

This downloads a pinned Hugging Face revision into:

```text
~/.lmstudio/models/sensenova/SenseNova-Loop-9B-Preview-GGUF/
  SenseNova-Loop-9B-Preview-Q8_0.gguf
```

For a custom model directory, use `--models-dir /path/to/your/models`. Use the directory configured in LM Studio. To check an existing download without network access:

```bash
python3 scripts/download_model.py --verify-only
```

The script verifies both the byte count and SHA256:

```text
7981be1e6e0d03b9f11bfc3b73eefa1a07a9e227acbac5402ee52b5dc8b82d68
```

## 3. Build the compatible library

For the tested CUDA 12.8 / GCC 14 / RTX 3090 configuration, set the paths to your installed tools:

```bash
export CC=gcc-14
export CXX=g++-14
export CUDACXX=/usr/local/cuda-12.8/bin/nvcc
export CUDAHOSTCXX=g++-14
export CUDA_ARCHITECTURES=86
export BUILD_JOBS=8
bash scripts/build_runtime.sh
```

Adjust those tool paths to your installation. CUDA architecture 86 is the RTX 3090 target; this guide does not claim testing on other GPU architectures.

The script creates a fresh `.work/llama.cpp-lmstudio` checkout at commit `ff0d396e3dda0f33e7ce5ad4267fce4f7690cfb1`, applies the Clover prerequisite and SenseNova patches in order, and builds with dynamic GGML backends. It refuses to reuse an existing source directory. For another build, set `SENSENOVA_WORK_DIR` to a new directory.

The Clover prerequisite reproduces the already-tested source tree. It is credited to Maphist0 and [llama.cpp PR #31306](https://github.com/ggml-org/llama.cpp/pull/31306); the downloaded model itself is SenseNova Loop.

## 4. Stage the custom runtime

```bash
python3 scripts/stage_runtime.py \
  --library .work/llama.cpp-lmstudio/build/bin/libllama.so
```

The script copies stock runtime 2.66.0 into `.work/staged/`, replaces only `libllama.so`, adjusts its loader names and search path, and labels the copy 2.66.101. It checks that existing public `llama_*` symbols are present and that the GGML library dependencies exist. Symbol checks alone do not prove ABI compatibility; this recipe relies on the pinned combination's recorded LM Studio test.

It retains LM Studio's wrappers and GGML libraries. Do not copy every library from the build into the runtime. No LM Studio vendor binaries are distributed in this repository.

## 5. Install the staged runtime

Save any active work, unload local models, and fully quit LM Studio, including its background service. If you use the standalone daemon, stop it with `lms daemon down`. This step interrupts local inference, so do it when your other sessions can stop.

From the recipe directory:

```bash
BACKENDS="$HOME/.lmstudio/extensions/backends"
CUSTOM="llama.cpp-linux-x86_64-nvidia-cuda12-avx2-2.66.101"
test -d "$BACKENDS" && test ! -e "$BACKENDS/$CUSTOM" && \
  cp -a ".work/staged/$CUSTOM" "$BACKENDS/$CUSTOM"
```

The command deliberately refuses to overwrite an existing custom runtime. If you already have 2.66.101 installed, keep it or stage a different local version with `--version 2.66.102`, updating the commands below accordingly.

Restart LM Studio, then select the custom runtime:

```bash
lms runtime ls
lms runtime select llama.cpp-linux-x86_64-nvidia-cuda12-avx2@2.66.101
```

Verify the custom version is selected. Changing the selected runtime also affects subsequent loads of other GGUF models; existing upstream model behavior is not guaranteed on every platform. Keep stock available for comparison and rollback.

## 6. Load SenseNova and chat

```bash
lms ls
lms load sensenova-loop-9b-preview@q8_0 \
  --gpu max --context-length 8192 --parallel 1 \
  --identifier sensenova-loop-9b --yes
lms chat sensenova-loop-9b --prompt 'What is 13 times 7?' \
  --reasoning off --dont-fetch-catalog --yes
```

Expected answer: `91`. If your model key differs, copy the exact key from `lms ls`. In the GUI, select the imported GGUF, use the embedded chat template, set an 8,192-token context and one parallel prediction, and disable thinking for these short smoke tests.

## 7. Use the local API

Start LM Studio's local server, then run the included Python example:

```bash
lms server start --port 1234
python3 scripts/smoke_test.py
```

If API authentication is enabled, set `LM_API_TOKEN` in your shell before running the example. If the loaded model has another identifier, pass `--model YOUR_IDENTIFIER`. The example uses the standard library and sends a request to `http://127.0.0.1:1234/v1/chat/completions`.

## Troubleshooting and rollback

| Symptom | What to check |
| --- | --- |
| `unknown model architecture: sensenova_loop` | Confirm the custom runtime is selected, then unload/reload this model. Downloading the GGUF alone does not add engine support. |
| Model absent from the list | Confirm the model directory in LM Studio matches `--models-dir`; refresh the local model list. |
| Missing symbol or shared library | Confirm stock 2.66.0 and the pinned source were used. Keep the stock GGML libraries and wrappers; do not substitute the newer upstream patch. |
| CUDA compiler rejects host compiler | Set `CC`, `CXX`, `CUDAHOSTCXX`, and `CUDACXX` to compatible installed versions. The recorded build used GCC 14 / CUDA 12.8. |
| Out of memory | Start with 8,192 context and one prediction; reduce context or GPU offload. Partial offload needs sufficient system RAM and has not been benchmarked here. |
| Custom runtime disappears | Check runtime automatic updates/cleanup and reinstall the staged copy while LM Studio is fully stopped. |
| Images, MTP, or diffusion options fail | These features are not implemented by this text-only adaptation. |
| No answer before token limit | Disable thinking for the smoke test, or increase the token limit. |

To roll back, unload SenseNova and select the stock runtime, or the previous runtime you recorded:

```bash
lms unload sensenova-loop-9b
lms runtime select llama.cpp-linux-x86_64-nvidia-cuda12-avx2@2.66.0
```

Stock 2.66.0 cannot load this custom architecture. Keep the downloaded model and staged runtime if you want to return later. Remove a custom runtime only after it is deselected and LM Studio is fully stopped.

## Code, validation, and attribution

- [Developer notes](DEVELOPMENT.md): architecture, patch provenance, separate upstream build, and test coverage.
- [Validation records](validation/): published model reference checks and CPU regression comparisons.
- [NOTICE](NOTICE): credits and licensing boundaries.

This repository's new scripts, documentation, and SenseNova adaptation use [Apache-2.0](LICENSE). Existing llama.cpp code and the Clover patch retain their [MIT license](licenses/llama.cpp-MIT.txt). Model weights remain under the original model's Apache-2.0 license and are downloaded from Hugging Face, not stored in GitHub. LM Studio retains its own licensing. This project is not endorsed by SenseNova, LM Studio, or the llama.cpp maintainers.
