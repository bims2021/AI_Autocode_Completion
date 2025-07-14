// tests/test_extension/integration.test.ts
import * as assert from 'assert';
import * as vscode from 'vscode';
import { TestSetup } from './setup';

suite('Integration Tests', () => {
    let testWorkspace: vscode.Uri;

    suiteSetup(async () => {
        testWorkspace = await TestSetup.createTestWorkspace();
        
        // Ensure extension is activated
        const extension = vscode.extensions.getExtension('your-publisher.python-code-autocompletion');
        if (extension && !extension.isActive) {
            await extension.activate();
        }
    });

    suiteTeardown(async () => {
        await TestSetup.cleanupTestWorkspace();
    });

    test('End-to-end completion workflow', async () => {
        // Open a Python file
        const document = await vscode.workspace.openTextDocument({
            language: 'python',
            content: 'def calculate_sum(a, b):\n    return a + b\n\ndef main():\n    result = calculate_'
        });

        const editor = await vscode.window.showTextDocument(document);
        
        // Position cursor at the end of 'calculate_'
        const position = new vscode.Position(3, 21);
        editor.selection = new vscode.Selection(position, position);

        // Trigger completion
        const completions = await vscode.commands.executeCommand(
            'vscode.executeCompletionItemProvider',
            document.uri,
            position
        );

        assert.ok(completions);
        assert.ok(Array.isArray(completions));
    });

    test('Configuration integration', async () => {
        const config = vscode.workspace.getConfiguration('pythonCodeAutocompletion');
        
        // Test configuration update
        await config.update('maxSuggestions', 3, vscode.ConfigurationTarget.Workspace);
        
        const updatedValue = config.get('maxSuggestions');
        assert.strictEqual(updatedValue, 3);
        
        // Reset to default
        await config.update('maxSuggestions', undefined, vscode.ConfigurationTarget.Workspace);
    });

    test('Multi-language support', async () => {
        const languages = ['python', 'javascript', 'typescript', 'java'];
        
        for (const lang of languages) {
            const document = await vscode.workspace.openTextDocument({
                language: lang,
                content: `// ${lang} test file\n`
            });

            // Check if language is recognized
            assert.strictEqual(document.languageId, lang);
        }
    });
});
