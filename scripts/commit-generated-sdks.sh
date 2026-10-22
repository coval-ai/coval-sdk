#!/usr/bin/env bash
set -euo pipefail

for validation in "$DETERMINISM" "$TYPESCRIPT_VALIDATION" "$PYTHON_VALIDATION"; do
  if [ "$validation" != success ]; then
    echo "SDK generation and both language validations must succeed before updating main." >&2
    exit 1
  fi
done
if [[ ! "$SOURCE_REF" =~ ^[0-9a-f]{40}$ ]]; then
  echo "A resolved backend commit is required." >&2
  exit 1
fi
if ! git diff --cached --quiet; then
  echo "Refusing to publish a checkout with pre-staged changes." >&2
  exit 1
fi

git fetch origin main:refs/remotes/origin/main
if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
  echo "Main changed during generation; republish through the backend workflow." >&2
  exit 1
fi
git add -- \
  typescript-sdk/src/generated \
  typescript-sdk/src/CovalClient.ts \
  python-sdk/src/coval_sdk \
  python-sdk/GENERATED_README.md
if git diff --cached --quiet; then
  echo "Generated SDKs are already current; no commit needed."
  exit 0
fi

git -c user.name='coval-release-automation[bot]' \
  -c user.email='330179580+coval-release-automation[bot]@users.noreply.github.com' \
  -c commit.gpgsign=false \
  commit -m 'fix(sdks): regenerate from published OpenAPI specs' \
  -m "Backend source: $SOURCE_REF"
git push origin HEAD:refs/heads/main
