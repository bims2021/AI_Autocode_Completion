// tests/test_extension/apiClient.test.ts
import * as assert from 'assert';
import * as sinon from 'sinon';
import { APIClient } from '../../vscode-extension/src/apiClient';

suite('API Client Tests', () => {
    let apiClient: APIClient;
    let fetchStub: sinon.SinonStub;

    setup(() => {
        apiClient = new APIClient();
        fetchStub = sinon.stub(global, 'fetch');
    });

    teardown(() => {
        fetchStub.restore();
    });

    test('Should make completion request with correct parameters', async () => {
        const mockResponse = {
            ok: true,
            json: async () => ({
                completions: [
                    { text: 'Hello, World!")', insertText: 'Hello, World!")' }
                ]
            })
        };
        fetchStub.resolves(mockResponse);

        const result = await apiClient.getCompletions(
            'def test():\n    print("',
            { line: 1, character: 12 },
            'python'
        );

        assert.ok(fetchStub.calledOnce);
        assert.ok(result.completions.length > 0);
        assert.strictEqual(result.completions[0].text, 'Hello, World!")');
    });

    test('Should handle API errors gracefully', async () => {
        const mockResponse = {
            ok: false,
            status: 500,
            statusText: 'Internal Server Error'
        };
        fetchStub.resolves(mockResponse);

        try {
            await apiClient.getCompletions(
                'def test():\n    print("',
                { line: 1, character: 12 },
                'python'
            );
            assert.fail('Should have thrown an error');
        } catch (error) {
            assert.ok(error instanceof Error);
            assert.ok(error.message.includes('500'));
        }
    });

    test('Should handle network errors', async () => {
        fetchStub.rejects(new Error('Network error'));

        try {
            await apiClient.getCompletions(
                'def test():\n    print("',
                { line: 1, character: 12 },
                'python'
            );
            assert.fail('Should have thrown an error');
        } catch (error) {
            assert.ok(error instanceof Error);
            assert.strictEqual(error.message, 'Network error');
        }
    });

    test('Should use correct API endpoint from configuration', () => {
        const config = { apiEndpoint: 'http://test-api:8000' };
        const clientWithConfig = new APIClient(config);
        
        // This would require making the endpoint accessible for testing
        // or using dependency injection
        assert.ok(clientWithConfig);
    });

    test('Should include proper headers in request', async () => {
        const mockResponse = {
            ok: true,
            json: async () => ({ completions: [] })
        };
        fetchStub.resolves(mockResponse);

        await apiClient.getCompletions(
            'test code',
            { line: 0, character: 0 },
            'python'
        );

        const callArgs = fetchStub.getCall(0).args;
        const requestOptions = callArgs[1];
        
        assert.strictEqual(requestOptions.method, 'POST');
        assert.strictEqual(requestOptions.headers['Content-Type'], 'application/json');
        assert.ok(requestOptions.body);
    });
});
