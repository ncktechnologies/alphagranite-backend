#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   BASE_URL="https://api.staging.odysseytracker.com/api/v1" \
#   BEARER_TOKEN="<jwt>" \
#   SCENARIO="load" \
#   ./perf/run-k6-staging.sh

BASE_URL="${BASE_URL:-https://api.staging.odysseytracker.com/api/v1}"
SCENARIO="${SCENARIO:-load}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${OUT_DIR:-${SCRIPT_DIR}/results}"
K6_SCRIPT="${SCRIPT_DIR}/k6/staging-api.js"
INSECURE_SKIP_TLS_VERIFY="${INSECURE_SKIP_TLS_VERIFY:-true}"
FAIL_ON_THRESHOLDS="${FAIL_ON_THRESHOLDS:-true}"

if [[ "${BASE_URL}" != http://* && "${BASE_URL}" != https://* ]]; then
  BASE_URL="https://${BASE_URL}"
fi

if [[ -z "${BEARER_TOKEN:-}" ]]; then
  echo "ERROR: BEARER_TOKEN is required"
  echo "Set it like: export BEARER_TOKEN='eyJ...'"
  exit 1
fi

if ! command -v k6 >/dev/null 2>&1; then
  echo "ERROR: k6 not found. Install from https://k6.io/docs/get-started/installation/"
  exit 1
fi

mkdir -p "${OUT_DIR}"
SUMMARY_JSON="${OUT_DIR}/summary_${SCENARIO}_${TIMESTAMP}.json"
RAW_JSON="${OUT_DIR}/raw_${SCENARIO}_${TIMESTAMP}.json"

echo "Running k6 scenario='${SCENARIO}' against '${BASE_URL}'"

K6_NO_THRESHOLDS_FLAG=()
if [[ "${FAIL_ON_THRESHOLDS,,}" == "false" ]]; then
  K6_NO_THRESHOLDS_FLAG+=("--no-thresholds")
fi

k6 run \
  "${K6_NO_THRESHOLDS_FLAG[@]}" \
  --env BASE_URL="${BASE_URL}" \
  --env BEARER_TOKEN="${BEARER_TOKEN}" \
  --env SCENARIO="${SCENARIO}" \
  --env INSECURE_SKIP_TLS_VERIFY="${INSECURE_SKIP_TLS_VERIFY}" \
  --env GLOBAL_P95_MS="${GLOBAL_P95_MS:-1200}" \
  --env GLOBAL_P99_MS="${GLOBAL_P99_MS:-2500}" \
  --env DASHBOARD_P95_MS="${DASHBOARD_P95_MS:-1200}" \
  --env FABS_P95_MS="${FABS_P95_MS:-2500}" \
  --env SHOP_PLANS_P95_MS="${SHOP_PLANS_P95_MS:-1800}" \
  --env FABS_PATH="${FABS_PATH:-/fabs?limit=25}" \
  --env DASHBOARD_PATH="${DASHBOARD_PATH:-/dashboard?time_period=this_week}" \
  --env SHOP_PLANS_PATH="${SHOP_PLANS_PATH:-/shop/plans?view=week&limit=50}" \
  --summary-export "${SUMMARY_JSON}" \
  --out json="${RAW_JSON}" \
  "${K6_SCRIPT}"

echo "Done."
echo "Summary: ${SUMMARY_JSON}"
echo "Raw data: ${RAW_JSON}"
