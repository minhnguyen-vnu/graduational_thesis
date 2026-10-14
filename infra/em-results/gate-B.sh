#!/usr/bin/env zsh
# Gate for the option-B fix. Phase 2 runs only if phase 1 passes, because a 21-row check on a build
# that did not fix the defect costs two hours and answers a question already answered.
set -u
B=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results
echo "=== GATE B start $(date) ==="
echo "jar under test: $(shasum -a 256 /Users/minhnguyen/IdeaProjects/EvoMaster/core/target/evomaster.jar | cut -c1-16)"
if $B/reproducibility/verify-B.sh; then
  echo "=== PHASE 1 PASS $(date) -- running the 21-row regression check ==="
  $B/regression-check/regression_check.sh
  echo "=== PHASE 2 exit=$? $(date) ==="
else
  echo "=== PHASE 1 FAIL $(date) -- phase 2 deliberately NOT run ==="
fi
echo "=== GATE B done $(date) ==="
