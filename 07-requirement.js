import http from 'k6/http';
import { check, sleep } from 'k6';

// P95 allows a second run with one deliberately stricter requirement.
export const options = {
  vus: 3,
  duration: '30s',
  thresholds: {
    http_req_duration: [`p(95)<${__ENV.P95 || 1000}`, 'p(99)<1500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.post('https://quickpizza.grafana.com/api/pizza',
    JSON.stringify({ mustBeVegetarian: true }), {
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'token abcdef0123456789',
      },
    });
  check(res, {
    'status is 200': (r) => r.status === 200,
    'pizza has a name': (r) => r.json('pizza.name') !== undefined,
  });
  sleep(1);
}
