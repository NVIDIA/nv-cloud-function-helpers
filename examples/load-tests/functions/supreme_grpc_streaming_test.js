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
    }
};


const client = new grpc.Client();
client.load(['definitions'], 'echo.proto');


export default () => {
    client.connect(`${__ENV.NVCF_GRPC_URL}`, { });

    const params = {
        metadata: {
            'function-id': `${__ENV.GRPC_SUPREME_FUNCTION_ID}`,
            'authorization': `Bearer ${__ENV.TOKEN}`
        },
    };
    const stream = new grpc.Stream(client, 'Echo/EchoMessageStreaming', params);

    const randomString = 'x'.repeat(__ENV.SENT_MESSAGE_SIZE)
    const req = { message: randomString, repeats: __ENV.RESPONSE_COUNT};

    stream.on('data', (message) => {
        check(message, {
            'message is echo': (message) => message && message.message === randomString,
        });
        // console.log("Received" + message.message);
    });

    stream.on('error', (err) => {
        check(err, {
            'error': (_) => false,
        });
        console.log('Stream Error: ' + JSON.stringify(err));
    });

    stream.on('end', () => {
        client.close();
    })

    for (let i = 0; i < __ENV.GRPC_SENT_MESSAGE_COUNT; i++) {
        stream.write(req);
    }

    stream.end();
};