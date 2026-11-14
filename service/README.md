# TPC-Council: HammerDB result submission proposal

**Status: awaiting TPC-Council administrator approval.** This branch proposes the
tested two-choice HammerDB submission form and the optional authorised
submission service. It does not change the working
`HammerDBLtd/hammerdb-results` site or Worker.

## What visitors see

- **I'll create my own PR**: the existing TPC-Council manual route — copy the
  enriched JSON, open the GitHub new-file editor, commit, and create a PR.
  This remains the default and works while automatic submission is disabled.
- **Do it for me**: once enabled, sign in to GitHub/authorise the submission
  App. The server verifies the authenticated GitHub account matches the
  declared `submission.github_username`, writes the JSON on a same-repository
  `submission/` branch, opens a PR, and sends the user to the PR. No fork,
  copied JSON, or manual GitHub commit is required.

The PR is reviewed and merged by a maintainer. Benchmark results remain
community-submitted and unaudited. **Neither option merges a result
automatically.** Until a public endpoint is configured,
`site/submission-service-config.js` is intentionally blank: the automatic
radio choice is disabled and the manual route stays usable.

## TPC-Council administrator decisions and approvals

1. **Review and approve** this code PR before merge. Decide who will operate
   the separate TPC submission service and whether TPC-Council approves a
   HammerDB Ltd-owned GitHub App acting in the TPC-Council results repository.
   An alternative TPC-owned GitHub App would require separate credentials and
   confirmation of its bot login.
2. If approved, **install and authorise** GitHub App
   `hammerdb-results-submit` (owned by HammerDB Ltd) for **only**
   `TPC-Council/hammerdb-results`. Required repository permissions:
   **Contents read/write**, **Pull requests read/write**, and Metadata read.
   Do not grant organisation-wide access unless the Council chooses to.
   No installation has yet been performed on TPC-Council.
3. Set TPC-Council repository **Actions variable**
   `SUBMISSION_APP_BOT_LOGIN` to `hammerdb-results-submit[bot]` (or the
   exact bot login of a different authorised App). CI only permits the
   App-specific attribution path when the PR author is this bot **and**
   the PR comes from a same-repository `submission/` branch. All
   human-authored PRs must still match their GitHub usernames.

## Separate TPC-only submission Worker — not yet deployed

The Worker operator, after Council approval, must:

1. Deploy `service/worker.mjs` to a **separate** Worker, for example
   `hammerdb-results-tpc-submit.hammerdb.workers.dev`. Do not rename,
   reconfigure, or reuse the working HammerDB Ltd submission Worker.
2. Create a **separate Cloudflare KV namespace** with binding `PENDING`.
   Set non-secret Worker variables `GITHUB_TARGET_OWNER=TPC-Council`,
   `GITHUB_TARGET_REPO=hammerdb-results`, and
   `ALLOWED_ORIGIN=https://tpc-council.github.io`.
3. Set Worker secrets `GITHUB_APP_CLIENT_ID`,
   `GITHUB_APP_CLIENT_SECRET`, `GITHUB_APP_PRIVATE_KEY` using the
   administrator-approved GitHub App's actual credentials. Never commit
   keys, passwords or tokens into the repository or public Pages files.
4. Add the TPC Worker's actual `/oauth/callback` address to the GitHub
   App's approved callback/redirect URLs **without replacing the working
   HammerDB Ltd callback**. Do not assume the placeholder Worker hostname
   is live until deployed.
5. Check the real TPC Worker `/health` reports
   `{"status":"ok","configured":true}`. Then conduct a real
   browser-to-GitHub end-to-end test against **TPC-Council only** with a
   new valid JSON. Confirm the PR opens under TPC-Council, a maintainer can
   review it, and all checks pass. Do **not merge a synthetic test result**.
6. Only after that, put the separately deployed TPC Worker **public URL
   only** in `site/submission-service-config.js`. This enables
   **Do it for me**; the existing manual route remains unchanged.

`service/wrangler.toml` contains a placeholder KV namespace ID. Replace it
with a real TPC-only KV ID if deploying with Wrangler. No additional DNS
changes are required when using a `workers.dev` address.

## Security boundaries

- The browser cannot choose the target repository: the Worker requires the
  exact configured TPC-Council owner/repo and validates the GitHub OAuth login.
- The submission payload is retained in private KV for at most 15 minutes.
  The Worker accepts submissions only from the exact configured origin.
- Duplicate result paths are blocked. Both routes require PR review.
- The existing HammerDB Ltd service, credentials, worker, and Pages remain
  untouched by this proposal.

## Automated tests

The TPC validation and Pages workflows now run the new frontend and Worker
tests alongside the existing result and annotation tests. The server-side
bot-identity tests preserve the existing manual-PR attribution checks.
