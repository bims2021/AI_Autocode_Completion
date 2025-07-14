// tests/test_extension/completionProvider.test.ts
import * as assert from 'assert';
import * as vscode from 'vscode';
import { CompletionProvider } from '../../vscode-extension/src/completionProvider';
import { TestSetup } from './setup';

suite('Completion Provider Tests', () => {
    let provider: CompletionProvider;
    let testWorkspace: vscode.Uri;

    suiteSetup(async () => {
        testWorkspace = await TestSetup.createTestWorkspace();
        provider = new CompletionProvider();
    });

    suiteTeardown(async () => {
        await TestSetup.cleanupTestWorkspace();
    });

    test('Should provide completions for Python files', async () => {
        // Create a test document
        const document = await vscode.workspace.openTextDocument({
            language: 'python',
            content: 'def test_func():\n    print("'
        });

        const position = new vscode.Position(1, 12);
        const completionList = await provider.provideCompletionItems(
            document,
            position,
            new vscode.CancellationToken(),
            { triggerKind: vscode.CompletionTriggerKind.Invoke }
        );

        assert.ok(completionList);
        if (completionList instanceof vscode.CompletionList) {
            assert.ok(completionList.items.length > 0);
        } else {
            assert.ok(completionList.length > 0);
        }
    });

    test('Should not provide completions for non-Python files', async () => {
        const document = await vscode.workspace.openTextDocument({
            language: 'javascript',
            content: 'function test() { console.log("'
        });

        const position = new vscode.Position(0, 31);
        const completionList = await provider.provideCompletionItems(
            document,
            position,
            new vscode.CancellationToken(),
            { triggerKind: vscode.CompletionTriggerKind.Invoke }
        );

        assert.strictEqual(completionList, null);
    });

    test('Should handle different trigger characters', async () => {
        const document = await vscode.workspace.openTextDocument({
            language: 'python',
            content: 'import numpy as np\nnp.'
        });

        const position = new vscode.Position(1, 3);
        const completionList = await provider.provideCompletionItems(
            document,
            position,
            new vscode.CancellationToken(),
            { 
                triggerKind: vscode.CompletionTriggerKind.TriggerCharacter,
                triggerCharacter: '.'
            }
        );

        assert.ok(completionList);
    });

    test('Should respect maxSuggestions configuration', async () => {
        const config = vscode.workspace.getConfiguration('pythonCodeAutocompletion');
        const maxSuggestions = config.get('maxSuggestions', 5);

        const document = await vscode.workspace.openTextDocument({
            language: 'python',
            content: 'def test():\n    '
        });

        const position = new vscode.Position(1, 4);
        const completionList = await provider.provideCompletionItems(
            document,
            position,
            new vscode.CancellationToken(),
            { triggerKind: vscode.CompletionTriggerKind.Invoke }
        );

        if (completionList) {
            const items = completionList instanceof vscode.CompletionList ? 
                completionList.items : completionList;
            assert.ok(items.length <= maxSuggestions);
        }
    });
});
