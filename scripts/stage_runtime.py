#!/usr/bin/env python3
"""Stage a custom runtime without changing the installed LM Studio runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

NAME = "llama.cpp-linux-x86_64-nvidia-cuda12-avx2"


def output(*args):
    return subprocess.check_output(args, text=True)


def exports(path):
    names = set()
    for line in output("nm", "-D", "--defined-only", str(path)).splitlines():
        fields = line.split()
        if fields:
            name = fields[-1].split("@")[0]
            if name.startswith("llama_"):
                names.add(name)
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--stock-runtime", type=Path, default=Path.home() / f".lmstudio/extensions/backends/{NAME}-2.66.0")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / ".work/staged")
    parser.add_argument("--version", default="2.66.101")
    args = parser.parse_args()
    if not re.fullmatch(r"2\.66\.\d{3,}", args.version):
        parser.error("Use a distinct local version such as 2.66.101")
    for tool in ("patchelf", "nm"):
        if not shutil.which(tool):
            parser.error(f"Missing dependency: {tool}")
    stock = args.stock_runtime.expanduser().resolve()
    library = args.library.expanduser().resolve(strict=True)
    manifest = json.loads((stock / "backend-manifest.json").read_text())
    if manifest.get("name") != NAME or manifest.get("version") != "2.66.0":
        parser.error("This integration is pinned to the stock CUDA 12 AVX2 runtime 2.66.0")
    old_exports, new_exports = exports(stock / "libllama.so"), exports(library)
    if not old_exports or old_exports - new_exports:
        parser.error(f"Public llama symbols missing: {sorted(old_exports - new_exports)}")
    output_dir = args.output_dir.expanduser().resolve()
    installed_backends = stock.parent
    if output_dir == installed_backends or installed_backends in output_dir.parents:
        parser.error("Stage outside the installed backend directory, then install after closing LM Studio")
    destination = output_dir / f"{NAME}-{args.version}"
    if destination.exists():
        parser.error(f"Refusing to overwrite {destination}")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".stage-", dir=output_dir) as temp:
        staged = Path(temp) / destination.name
        shutil.copytree(stock, staged, symlinks=True)
        target_library = staged / "libllama.so"
        target_library.unlink()
        shutil.copy2(library, target_library)
        subprocess.run([
            "patchelf", "--set-soname", "libllama.so", "--set-rpath", "$ORIGIN",
            "--replace-needed", "libggml.so.0", "libggml_llamacpp.so",
            "--replace-needed", "libggml-base.so.0", "libggml-base.so", str(target_library)
        ], check=True)
        needed = output("patchelf", "--print-needed", str(target_library)).splitlines()
        for name in needed:
            if name.startswith("libggml") and not (staged / name).is_file():
                raise RuntimeError(f"Missing runtime dependency: {name}")
        manifest["version"] = args.version
        (staged / "backend-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        display = [["en", {
            "langKey": "en", "displayName": "CUDA 12 llama.cpp (SenseNova Loop + Clover)",
            "description": "Unofficial SenseNova Loop text support, based on runtime 2.66.0",
            "releaseNotes": [{"version": args.version, "releaseNotes": "Expanded loop layers and two-stream mHC. Text only."}]
        }]]
        (staged / "display-data.json").write_text(json.dumps(display, indent=2) + "\n")
        with target_library.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        (staged / "sensenova-build.json").write_text(json.dumps({
            "base_revision": "ff0d396e3dda0f33e7ce5ad4267fce4f7690cfb1",
            "stock_runtime": "2.66.0", "custom_runtime": args.version,
            "libllama_sha256": checksum, "exported_llama_symbols_checked": len(old_exports),
            "note": "Symbol presence is a compatibility check, not proof of ABI compatibility."
        }, indent=2) + "\n")
        staged.rename(destination)
    print(f"Staged: {destination}\nRuntime identifier: {NAME}@{args.version}")
    print("Close LM Studio and its background service before copying this directory into its backends directory.")


if __name__ == "__main__":
    main()
