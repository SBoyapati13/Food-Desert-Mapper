"""Scheduled update: fetch new or revised sources, rebuild if anything changed (or outputs are missing), rebuild the site.

    python3 src/update.py            # every state in config/states.json
    python3 src/update.py NJ --force # rebuild even with no new data

Unchanged sources are not downloaded; a rebuild on a fresh runner downloads the cached files it needs and checks
them against the committed SHA-256 hashes.
"""
import sys
from pathlib import Path
import fetch, build, web

ROOT = Path(__file__).resolve().parents[1]

def main(args):
    force = "--force" in args
    sts = [a for a in args if not a.startswith("--")] or list(fetch.states().keys())
    for st in sts:
        changed, errors = fetch.sync(st)
        print(f"{st}: new or revised {changed or 'none'}" + (f"; problems (previous copies kept): {errors}" if errors else ""))
        if force or changed or not (ROOT / "out" / st / "summary.json").exists():
            build.main(st)
        web.main(st)
    web.index()

if __name__ == "__main__":
    main(sys.argv[1:])
