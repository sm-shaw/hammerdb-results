# HammerDB Results Prototype for TPC-OSS

This repository is a **prototype** for a future TPC-Council HammerDB results workflow.

- Current prototype repo: this repository under a personal GitHub account.
- Intended live repo: https://github.com/TPC-Council/hammerdb-results
- Intended live GitHub Pages site: https://tpc-council.github.io/hammerdb-results/
- Official public entry point: TPC HammerDB Artifact Results page at https://www.tpc.org/opensource/opensource5.asp

This prototype demonstrates GitHub-authenticated submission and CI validation for HammerDB `summaryjson` artifacts. GitHub provides authenticated submission, identity, timestamping, review history, validation checks, and anti-spam control.

This prototype does **not** imply that this prototype GitHub Pages site is the final TPC website.

Results are community-submitted HammerDB results, unaudited, and not official TPC benchmark results.

## Contributor workflow

1. Star the HammerDB project at https://github.com/TPC-Council/HammerDB
2. Generate a HammerDB `summaryjson` artifact
3. Add the artifact under `results/`
4. Open a pull request
5. GitHub Actions validates the artifact before review/publication

## Submit a HammerDB result artifact

Use this repository workflow to submit a HammerDB result artifact through a GitHub pull request.

## Local commands

```bash
python tools/validate_result.py
python tools/build_leaderboard.py
```

## What happens after a PR is opened?

1. GitHub Actions runs `.github/workflows/validate.yml`.
2. CI runs validation and leaderboard generation.
3. If validation fails, the PR is blocked until fixed.
4. If validation passes, maintainers review and can merge.
5. On merge to the default branch (`master` in this prototype), `.github/workflows/publish.yml` runs to validate/build again and publish `site/`.

## End-to-end flow

HammerDB benchmark run
-> HammerDB Benchmark Report
-> summaryjson artifact
-> GitHub-authenticated pull request
-> validation by GitHub Actions
-> TPC-OSS review/merge
-> generated leaderboard data
-> TPC website leaderboard

## Brand/publication path for the future live flow

TPC HammerDB Artifact Results page
-> TPC-Council/hammerdb-results GitHub Pages
-> Submit a HammerDB result artifact
-> Star TPC-Council/HammerDB
-> Open a validated GitHub PR

## Future Share with TPC-OSS flow

- User clicks “Share with TPC-OSS” in HammerDB.
- If the HammerDB server is public, the submission flow can use the summaryjson URL.
- If HammerDB is running locally, the browser or CLI posts the summaryjson artifact.
- The user authenticates with GitHub.
- The artifact is submitted as a GitHub pull request.
- GitHub provides identity, timestamp, anti-spam, and review history.
- TPC-OSS reviews and accepts the result.
- The TPC website publishes accepted results.

## Important UI note

The HammerDB UI should say “Share with TPC-OSS”, not “Save as JSON”. The JSON is the machine-readable submission artifact behind the scenes.
