#!/usr/bin/env bash
set -euo pipefail

recipe_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
work_dir=${SENSENOVA_WORK_DIR:-"$recipe_root/.work"}
source_dir="$work_dir/llama.cpp-lmstudio"
base_revision=ff0d396e3dda0f33e7ce5ad4267fce4f7690cfb1

for command in git cmake ninja; do
    command -v "$command" >/dev/null || { echo "Missing dependency: $command" >&2; exit 1; }
done
mkdir -p "$work_dir"
if [[ -e "$source_dir" ]]; then
    echo "Refusing to reuse $source_dir. Choose a fresh SENSENOVA_WORK_DIR." >&2
    exit 1
fi
git init "$source_dir"
git -C "$source_dir" remote add origin https://github.com/ggml-org/llama.cpp.git
git -C "$source_dir" fetch --depth 1 origin "$base_revision"
git -C "$source_dir" checkout --detach FETCH_HEAD
git -C "$source_dir" apply "$recipe_root/patches/lmstudio/01-clover-pr31306.patch"
git -C "$source_dir" apply "$recipe_root/patches/lmstudio/02-sensenova-loop-native.patch"

# Set CC, CXX, CUDACXX and CUDAHOSTCXX before calling this script as needed.
cmake -S "$source_dir" -B "$source_dir/build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
    -DGGML_CUDA=ON -DGGML_BACKEND_DL=ON -DGGML_NATIVE=OFF \
    -DCMAKE_CUDA_ARCHITECTURES="${CUDA_ARCHITECTURES:-86}"
cmake --build "$source_dir/build" --parallel "${BUILD_JOBS:-8}" \
    --target llama llama-cli llama-server llama-quantize
echo "Built library: $source_dir/build/bin/libllama.so"
