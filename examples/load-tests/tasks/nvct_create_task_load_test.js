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
                threshold: 'avg<5000', // string
                abortOnFail: true, // boolean
            },
        ],
    },
};

export default function() {
    let response

    // choose a random number of minutes between 2 and 10
    const numOfMinutes = Math.floor(Math.random() * 8) + 2;

    const payload = JSON.stringify({
        "name": `test_create_task_load_${numOfMinutes}m`,
    	"containerImage": `stg.nvcr.io/${__ENV.ORG_ID}/tasks_sample:0.0.5`,
        "containerEnvironment": [
            {
                "key": "NUM_OF_RESULTS",
                "value": numOfMinutes.toString()  // this ends up being the number of minutes the task will run for
            },
        ],
        "gpuSpecification": {
            "gpu": "T10",
            "instanceType": "g6.full",
            "backend": "GFN"
        },
        "maxRuntimeDuration": "PT1H",
        "maxQueuedDuration": "PT2H",
        "terminationGracePeriodDuration": "PT15M",
        "resultHandlingStrategy":"NONE"
    });

    const headers = {
        headers: {
            'Authorization': `Bearer ${__ENV.TOKEN}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
    };

    const url = `${__ENV.BASE_URL}/v2/orgs/${__ENV.ORG_ID}/nvct/tasks`

    response = http.post(
        url, payload, headers
    )
    const statusIsOk = check(response, {
        'status code MUST be 200': (response) => response.status === 200,
    })

    if (!statusIsOk) {
        console.error('Check failed:', response.status);
        console.error('Response:', response.body);
    }

    sleep(1)
}
