// tests/test_extension/config.test.ts
import * as assert from 'assert';
import * as vscode from 'vscode';
import { ConfigManager } from '../../vscode-extension/src/config';

suite('Configuration Tests', () => {
    let configManager: ConfigManager;

    setup(() => {
        configManager = new ConfigManager();
    });

    test('Should load default configuration', () => {
        const config = configManager.getConfiguration();
        
        assert.strictEqual(config.enabled, true);
        assert.strictEqual(config.apiEndpoint, 'http://localhost:8000');
        assert.strictEqual(config.maxSuggestions, 5);
        assert.strictEqual(config.requestTimeout, 5000);
        assert.strictEqual(config.enableLogging, false);
    });

    test('Should handle configuration changes', (done) => {
        const disposable = configManager.onConfigurationChanged((config) => {
            assert.ok(config);
            disposable.dispose();
            done();
        });

        // Simulate configuration change
        configManager.updateConfiguration({ enabled: false });
    });

    test('Should validate configuration values', () => {
        const validConfig = {
            enabled: true,
            apiEndpoint: 'http://localhost:8000',
            maxSuggestions: 10,
            requestTimeout: 3000,
            enableLogging: true
        };

        const isValid = configManager.validateConfiguration(validConfig);
        assert.strictEqual(isValid, true);
    });

    test('Should reject invalid configuration', () => {
        const invalidConfig = {
            enabled: 'true', // Should be boolean
            apiEndpoint: 'invalid-url',
            maxSuggestions: -1, // Should be positive
            requestTimeout: 'fast' // Should be number
        };

        const isValid = configManager.validateConfiguration(invalidConfig);
        assert.strictEqual(isValid, false);
    });

    test('Should get language-specific configuration', () => {
        const pythonConfig = configManager.getLanguageConfiguration('python');
        assert.ok(pythonConfig);
        assert.strictEqual(pythonConfig.language, 'python');
    });
});

