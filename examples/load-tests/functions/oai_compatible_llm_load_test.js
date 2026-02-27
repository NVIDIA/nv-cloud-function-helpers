import { sleep, check } from 'k6'
import http from 'k6/http'

export const options = {
    thresholds: {
        // Rate: content must be OK more than 95 times
        checks: [
            {
                threshold: 'rate>0.99', // string
                abortOnFail: true, // boolean
            },
        ],
        // Trend: Percentiles, averages, medians, and minimums
        // must be within specified milliseconds.
        http_req_duration: [
            {
                threshold: 'avg<15000', // string
                abortOnFail: true, // boolean
            },
        ],
    },
};

export default function() {
    let response

    const payload = `{
        "model": ${__ENV.LLM_MODEL_NAME},
        "messages": [
            {
                "content": "What should I see in Paris?",
                "role": "user",
            }
        ],
        "temperature": 0.2,
        "top_p": 0.7,
        "max_tokens": 1024,
        "stream": false,
    }`

    const params = {
        headers: {
            'Authorization': `Bearer ${__ENV.TOKEN}`,
            'Content-Type': 'application/json'
        },
    };

    const url = `${__ENV.OAI_COMPAT_URL}`

    response = http.post(
        url, payload, params
    )
    const statusIsOk = check(response, {
        'status code MUST be 200': (response) => response.status === 200,
    })

    if (!statusIsOk) {
        console.error('Check failed:', response.body);
    }

    sleep(0.001)
}