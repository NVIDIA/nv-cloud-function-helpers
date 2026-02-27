import { check } from 'k6'
import http from 'k6/http'

export const options = {
    thresholds: {
        checks: [
            {
                threshold: 'rate>0.99', // string
                abortOnFail: true, // boolean
            },
        ],
        http_req_duration: [
            {
                threshold: 'avg<15000', // string
                abortOnFail: true, // boolean
            },
        ],
    },
};

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

    const url = `${__ENV.HTTP_SUPREME_NVCF_URL}`

    response = http.post(
        url, payload, params
    )

    const statusIsOk = check(response, {
        'status code MUST be 200': (response) => response.status === 200,
    })

    if (!statusIsOk) {
        console.error('Check failed:', response);
    }
}