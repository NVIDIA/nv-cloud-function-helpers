import { sleep, check } from 'k6'
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
                threshold: 'avg<1000', // string
                abortOnFail: true, // boolean
            },
        ],
    },
};

export default function() {
    let response

    const url = `${__ENV.OAI_COMPAT_URL}` // ex: https://integrate.api.nvidia.com/v1/models

    response = http.get(url)
    const statusIsOk = check(response, {
        'status code MUST be 200': (response) => response.status === 200,
    })

    if (!statusIsOk) {
        console.error('Check failed:', response.body);
    }

    sleep(0.001)
}