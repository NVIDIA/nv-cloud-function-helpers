import { check } from 'k6'
import http from 'k6/http'
import { Trend } from 'k6/metrics';

export const TrendReturnedResponsesPerSecondPerVU = new Trend('TrendReturnedResponsesPerSecondPerVU');
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
                threshold: 'avg<5000', // string
                abortOnFail: true, // boolean
            },
        ],
    }
};


function memoizeRepeat() {
    const cache = {};

    return function(stringSize) {
        if (!(stringSize in cache)) {
            cache[stringSize] = 'x'.repeat(stringSize);
        }
        return cache[stringSize];
    };
}

const memoizedRepeat = memoizeRepeat();

export default function() {
    let response

    const randomString = memoizedRepeat(__ENV.SENT_MESSAGE_SIZE)

    const payload = `{
        "message": "${randomString}",
        "repeats": ${Number(__ENV.RESPONSE_COUNT)},
        "stream": true
    }`

    const params = {
        timeout: 30 * 1000, //milliseconds
        headers: {
            'Authorization': `Bearer ${__ENV.TOKEN}`,
            'Content-Type': 'application/json',
            'NVCF-POLL-SECONDS': '30',
            'Accept': 'text/event-stream'
        },
    };

    const url = `${__ENV.HTTP_SUPREME_NVCF_URL}`

    response = http.post(
        url, payload, params
    )
    const statusIsOk = check(response, {
        'status code MUST be 200': (response) => response.status === 200,
    })

    if (!statusIsOk) {
        console.error('Check failed:', response.body);
    }

    TrendReturnedResponsesPerSecondPerVU.add(`${__ENV.RESPONSE_COUNT}`/response.timings.duration*1000);
}