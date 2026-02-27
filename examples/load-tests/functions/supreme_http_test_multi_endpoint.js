import { check } from 'k6'
import http from 'k6/http'
import { Counter } from 'k6/metrics'

export const options = {
    thresholds: {
        checks: [
            {
                threshold: 'rate>0.99',
                abortOnFail: true,
            },
        ],
        http_req_duration: [
            {
                threshold: 'avg<15000',
                abortOnFail: true,
            },
        ],
        endpoint_requests: ['count>=0'],
    },
};

const endpoints = __ENV.ENDPOINTS ? __ENV.ENDPOINTS.split(',').map(e => e.trim()).filter(Boolean) : [];

if (endpoints.length === 0) {
    throw new Error('No endpoints provided. Set ENDPOINTS environment variable with comma-separated URLs.');
}

const endpointRequests = new Counter('endpoint_requests');

function memoizePayload() {
    let cache = null;

    return function() {
        if (cache === null) {
            const payloadObj = {
                "message": 'x'.repeat(__ENV.SENT_MESSAGE_SIZE),
                "repeats": Number(__ENV.RESPONSE_COUNT),
            };
            if (__ENV.RESPONSE_DELAY_TIME) {
                payloadObj.delay = Number(__ENV.RESPONSE_DELAY_TIME);
            }
            cache = JSON.stringify(payloadObj);
        }
        return cache;
    };
}

const getPayload = memoizePayload();

function selectRandomEndpoint(endpoints) {
    const randomIndex = Math.floor(Math.random() * endpoints.length);
    return endpoints[randomIndex];
}

const params = {
    timeout: 300 * 1000, //milliseconds
    headers: {
        'Authorization': `Bearer ${__ENV.TOKEN}`,
        'Content-Type': 'application/json',
        'NVCF-POLL-SECONDS': '300'
    },
};

export default function() {
    let response

    const payload = getPayload();

    const url = selectRandomEndpoint(endpoints)

    response = http.post(
        url, payload, params
    )

    endpointRequests.add(1, { endpoint: url });

    const statusIsOk = check(response, {
        'status code MUST be 200': (response) => response.status === 200,
    })

    if (!statusIsOk) {
        console.error('Check failed:', response);
    }
}
