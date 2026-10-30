#!/usr/bin/env python3
"""Exercise the model through LM Studio's local OpenAI-compatible endpoint."""
import argparse
import json
import os
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--model", default="sensenova-loop-9b")
    args = parser.parse_args()
    headers = {"Content-Type": "application/json"}
    if os.environ.get("LM_API_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["LM_API_TOKEN"]
    payload = {"model": args.model, "messages": [
        {"role": "user", "content": "What is 13 times 7? Give only the number."}
    ], "temperature": 0, "max_tokens": 256}
    request = urllib.request.Request(args.base_url.rstrip("/") + "/chat/completions",
                                     data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)
    message = result["choices"][0]["message"]
    content = message.get("content") or ""
    print(content)
    if not content.strip():
        raise SystemExit("No visible response. Disable thinking in LM Studio or raise max_tokens.")
    print("API request completed. Check that the answer is 91; this is a smoke test, not a quality benchmark.")


if __name__ == "__main__":
    main()
