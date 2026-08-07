import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const baseUrlRaw = (__ENV.BASE_URL || 'https://api.staging.odysseytracker.com/api/v1').trim();
const baseUrl = baseUrlRaw.startsWith('http://') || baseUrlRaw.startsWith('https://')
  ? baseUrlRaw
  : `https://${baseUrlRaw}`;

const bearerToken = (__ENV.BEARER_TOKEN || '').trim();
const scenario = (__ENV.SCENARIO || 'load').trim().toLowerCase();
const insecureSkipTlsVerify = ((__ENV.INSECURE_SKIP_TLS_VERIFY || 'true').trim().toLowerCase() === 'true');

const fabsPath = __ENV.FABS_PATH || '/fabs?limit=25';
const dashboardPath = __ENV.DASHBOARD_PATH || '/dashboard?time_period=this_week';
const shopPlansPath = __ENV.SHOP_PLANS_PATH || '/shop/plans?view=week&limit=50';
const globalP95Ms = Number(__ENV.GLOBAL_P95_MS || 1200);
const globalP99Ms = Number(__ENV.GLOBAL_P99_MS || 2500);
const dashboardP95Ms = Number(__ENV.DASHBOARD_P95_MS || 1200);
const fabsP95Ms = Number(__ENV.FABS_P95_MS || 2500);
const shopPlansP95Ms = Number(__ENV.SHOP_PLANS_P95_MS || 1800);

const dashboardDuration = new Trend('endpoint_dashboard_duration', true);
const fabsDuration = new Trend('endpoint_fabs_duration', true);
const shopPlansDuration = new Trend('endpoint_shop_plans_duration', true);

const scenarioProfiles = {
  smoke: {
    executor: 'constant-vus',
    vus: 1,
    duration: '30s',
  },
  load: {
    executor: 'ramping-vus',
    stages: [
      { duration: '1m', target: 10 },
      { duration: '3m', target: 30 },
      { duration: '2m', target: 30 },
      { duration: '1m', target: 0 },
    ],
  },
  stress: {
    executor: 'ramping-vus',
    stages: [
      { duration: '1m', target: 25 },
      { duration: '2m', target: 75 },
      { duration: '2m', target: 150 },
      { duration: '2m', target: 0 },
    ],
  },
  soak: {
    executor: 'constant-vus',
    vus: 20,
    duration: '20m',
  },
};

const selectedScenario = scenarioProfiles[scenario] || scenarioProfiles.load;

export const options = {
  insecureSkipTLSVerify: insecureSkipTlsVerify,
  scenarios: {
    api: selectedScenario,
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: [`p(95)<${globalP95Ms}`, `p(99)<${globalP99Ms}`],
    endpoint_dashboard_duration: [`p(95)<${dashboardP95Ms}`],
    endpoint_fabs_duration: [`p(95)<${fabsP95Ms}`],
    endpoint_shop_plans_duration: [`p(95)<${shopPlansP95Ms}`],
    checks: ['rate>0.95'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

function authHeaders() {
  return {
    Authorization: `Bearer ${bearerToken}`,
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };
}

function get(url, tags) {
  const res = http.get(url, {
    headers: authHeaders(),
    tags,
    timeout: '60s',
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  const endpoint = (tags && tags.endpoint) || '';
  if (endpoint === 'dashboard') {
    dashboardDuration.add(res.timings.duration);
  } else if (endpoint === 'fabs') {
    fabsDuration.add(res.timings.duration);
  } else if (endpoint === 'shop-plans') {
    shopPlansDuration.add(res.timings.duration);
  }

  return res;
}

export function setup() {
  if (!bearerToken) {
    throw new Error('BEARER_TOKEN is required');
  }

  // Quick authentication sanity check before starting the full scenario.
  const ping = http.get(`${baseUrl}${dashboardPath}`, {
    headers: authHeaders(),
    tags: { endpoint: 'dashboard-setup' },
    timeout: '30s',
  });

  const ok = ping.status === 200;
  if (!ok) {
    throw new Error(`Initial auth/request failed. Expected 200, got ${ping.status}. Response: ${ping.body}`);
  }
}

export default function () {
  get(`${baseUrl}${dashboardPath}`, { endpoint: 'dashboard' });
  sleep(0.2);

  get(`${baseUrl}${fabsPath}`, { endpoint: 'fabs' });
  sleep(0.2);

  get(`${baseUrl}${shopPlansPath}`, { endpoint: 'shop-plans' });
  sleep(0.4);
}
