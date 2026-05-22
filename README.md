# HammerDB Results Prototype for TPC-OSS

This repository is a **small prototype** that proves one thing:

> A HammerDB `summaryjson` artifact can be submitted through GitHub, validated by CI, and turned into leaderboard data for later use on the TPC website.

It is intentionally minimal and dependency-free (Python standard library only).

## What this repo is (and is not)

- ✅ **Is:** GitHub-side submission, validation, and leaderboard export prototype.
- ❌ **Is not:** The final TPC website.
- ❌ **Is not:** A source of official TPC benchmark results.

All results here are:

- Community-submitted HammerDB results
- Unaudited
- Not official TPC benchmark results

## The 2 commands you use locally

From repository root:

```bash
python tools/validate_result.py
python tools/build_leaderboard.py
```

What each command does:

- `validate_result.py`
  - Reads every `results/**/*.json`
  - Verifies required fields and path conventions
  - Fails with clear errors if something is wrong
- `build_leaderboard.py`
  - Reads the same `results/**/*.json`
  - Builds leaderboard output files:
    - `site/leaderboard.json`
    - `site/index.html`

## Typical contributor workflow (simple)

1. Add a HammerDB `summaryjson` file under `results/...`.
2. Run local checks:
   - `python tools/validate_result.py`
   - `python tools/build_leaderboard.py`
3. Commit your changes and open a pull request.

## What happens after a PR is opened?

1. GitHub Actions runs `.github/workflows/validate.yml`.
2. CI runs:
   - `python tools/validate_result.py`
   - `python tools/build_leaderboard.py`
   - JSON syntax check for `site/leaderboard.json`
3. If validation fails, the PR is blocked until fixed.
4. If validation passes, maintainers review and can merge.
5. On merge to default branch (`main`), `.github/workflows/publish.yml` runs:
   - validates again
   - rebuilds leaderboard
   - publishes `site/` via GitHub Pages actions

So the PR is the controlled submission gate: identity, timestamp, anti-spam, and review history all come from GitHub.

## End-to-end flow

HammerDB benchmark run
-> HammerDB Benchmark Report
-> summaryjson artifact
-> GitHub-authenticated pull request
-> validation by GitHub Actions
-> TPC-OSS review/merge
-> generated leaderboard data
-> TPC website leaderboard

## Future Share with TPC-OSS flow

- User clicks “Share with TPC-OSS” in HammerDB.
- If the HammerDB server is public, the submission flow can use the summaryjson URL.
- If HammerDB is running locally, the browser or CLI posts the summaryjson artifact.
- The user authenticates with GitHub.
- The artifact is submitted as a GitHub pull request.
- GitHub provides identity, timestamp, anti-spam, and review history.
- TPC-OSS reviews and accepts the result.
- The TPC website publishes accepted results.

## File map (quick reference)

- `results/` — submitted HammerDB summaryjson artifacts
- `tools/validate_result.py` — validation logic
- `tools/build_leaderboard.py` — leaderboard generation
- `site/leaderboard.json` — generated machine-readable leaderboard
- `site/index.html` — generated static leaderboard page
- `.github/workflows/validate.yml` — CI on push/PR
- `.github/workflows/publish.yml` — CI + Pages publish on `main`

## GitHub Pages note

The publish workflow is set up to deploy `site/` using GitHub Actions Pages deployment. If needed, repository Pages settings should be configured to use GitHub Actions as source.

## Important UI note

The HammerDB UI should say “Share with TPC-OSS”, not “Save as JSON”. The JSON is the machine-readable submission artifact behind the scenes.
