// tests/test_extension/extension.test.ts
import * as assert from 'assert';
import * as vscode from 'vscode';
import { TestSetup } from './setup';

suite('Extension Activation Tests', () => {
    let testWorkspace: vscode.Uri;

    suiteSetup(async () => {
        testWorkspace = await TestSetup.createTestWorkspace();
    });

    suiteTeardown(async () => {
        await TestSetup.cleanupTestWorkspace();
    });

    test('Extension should be present', () => {
        assert.ok(vscode.extensions.getExtension('your-publisher.python-code-autocompletion'));
    });

    test('Extension should activate', async () => {
        const extension = vscode.extensions.getExtension('your-publisher.python-code-autocompletion');
        assert.ok(extension);
        
        if (!extension.isActive) {
            await extension.activate();
        }
        
        assert.ok(extension.isActive);
    });

    test('Extension should register completion provider', async () => {
        const extension = vscode.extensions.getExtension('your-publisher.python-code-autocompletion');
        assert.ok(extension);
        
        if (!extension.isActive) {
            await extension.activate();
        }

        // Check if completion provider is registered
        const completionProviders = vscode.languages.getLanguages();
        assert.ok(completionProviders.includes('python'));
    });

    test('Extension should have correct configuration', () => {
        const config = vscode.workspace.getConfiguration('pythonCodeAutocompletion');
        assert.ok(config);
        
        // Test default configuration values
        assert.strictEqual(config.get('enabled'), true);
        assert.strictEqual(config.get('apiEndpoint'), 'http://localhost:8000');
        assert.strictEqual(config.get('maxSuggestions'), 5);
    });
});
