import grpc from 'k6/net/grpc';
import { check } from 'k6';

export const options = {
    thresholds: {
        checks: [
            {
                threshold: 'rate>0.99', // string
                abortOnFail: true, // boolean
            },
        ],
        grpc_req_duration: [
            {
                threshold: 'avg<5000', // string
                abortOnFail: true, // boolean
            },
        ],
    },
};


const client = new grpc.Client();
client.load(['definitions'], 'echo.proto');


export default () => {
    client.connect(`${__ENV.NVCF_GRPC_URL}`, {
        plaintext: __ENV.GRPC_PLAINTEXT === 'true',
    });

    const metadata = {
        'function-id': `${__ENV.GRPC_SUPREME_FUNCTION_ID}`,
        'authorization': `Bearer ${__ENV.TOKEN}`,
    };
    if (__ENV.GRPC_SUPREME_FUNCTION_VERSION_ID) {
        metadata['function-version-id'] = `${__ENV.GRPC_SUPREME_FUNCTION_VERSION_ID}`;
    }

    const params = { metadata };
    const randomString = 'x'.repeat(__ENV.SENT_MESSAGE_SIZE)
    const req = { message: randomString, repeats: __ENV.RESPONSE_COUNT };
    const response = client.invoke('Echo/EchoMessage', req, params);

    const statusIsOk = check(response, {
        'status is OK': (r) => r && r.status === grpc.StatusOK,
    });

    if (!statusIsOk) {
        console.error('Check failed:', response.error);
    }

    // console.log(JSON.stringify(response.message));
    // console.log(JSON.stringify(response.error));

    client.close();
};