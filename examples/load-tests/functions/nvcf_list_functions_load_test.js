import { sleep, check } from 'k6'
import http from 'k6/http'

export const options = {
    // thresholds: {
    //     // Rate: content must be OK more than 95 times
    //     checks: [
    //         {
    //             threshold: 'rate>0.99', // string
    //             abortOnFail: true, // boolean
    //         },
    //     ],
    //     // Trend: Percentiles, averages, medians, and minimums
    //     // must be within specified milliseconds.
    //     http_req_duration: [
    //         {
    //             threshold: 'avg<15000', // string
    //             abortOnFail: true, // boolean
    //         },
    //     ],
    // },
};

export default function() {
    let response

    const headers = {
        headers: {
            'Authorization': 'Bearer ',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
    };

    let url = 'https://stg.api.nvcf.nvidia.com/v2/nvcf/accounts/JYdkpexyfPh6kAxtPc1Fa2dPr4jfFdlXLTzm1De0LFk/functions'

    response = http.get(
        url, headers
    )
    const statusIsOk = check(response, {
        'status code MUST be 200': (response) => response.status === 200,
    })

    if (!statusIsOk) {
        console.error('Check failed:', response.status);
    }

    sleep(0.001)
}


