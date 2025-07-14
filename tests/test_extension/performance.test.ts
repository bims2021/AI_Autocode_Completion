// tests/test_extension/performance.test.ts
import * as assert from 'assert';
import * as vscode from 'vscode';
import { TestSetup } from './setup';

suite('Performance Tests', () => {
    let testWorkspace: vscode.Uri;

    suiteSetup(async () => {
        testWorkspace = await TestSetup.createTestWorkspace();
    });

    suiteTeardown(async () => {
        await TestSetup.cleanupTestWorkspace();
    });

    test('Completion response time should be reasonable', async () => {
        const document = await vscode.workspace.openTextDocument({
            language: 'python',
            content: 'def test_function():\n    '
        });

        const position = new vscode.Position(1, 4);
        const startTime = Date.now();

        const completions = await vscode.commands.executeCommand(
            'vscode.executeCompletionItemProvider',
            document.uri,
            position
        );

        const endTime = Date.now();
        const responseTime = endTime - startTime;

        assert.ok(completions);
        assert.ok(responseTime < 5000, `Response time ${responseTime}ms is too slow`);
    });

    test('Should handle large files efficiently', async () => {
        // Create a large Python file
        const largeContent = Array(1000).fill(0).map((_, i) => 
            `def function_${i}():\n    return ${i}\n`
        ).join('\n');

        const document = await vscode.workspace.openTextDocument({
            language: 'python',
            content: largeContent + '\n# Add completion here: '
        });

        const position = new vscode.Position(document.lineCount - 1, 25);
        const startTime = Date.now();

        const completions = await vscode.commands.executeCommand(
            'vscode.executeCompletionItemProvider',
            document.uri,
            position
        );

        const endTime = Date.now();
        const responseTime = endTime - startTime;

        assert.ok(completions);
        assert.ok(responseTime < 10000, `Large file response time ${responseTime}ms is too slow`);
    });

    test('Should handle concurrent requests', async () => {
        const documents = await Promise.all([
            vscode.workspace.openTextDocument({ language: 'python', content: 'def test1():\n    ' }),
            vscode.workspace.openTextDocument({ language: 'python', content: 'def test2():\n    ' }),
            vscode.workspace.openTextDocument({ language: 'python', content: 'def test3():\n    ' })
        ]);

        const position = new vscode.Position(1, 4);
        const startTime = Date.now();

        const completionPromises = documents.map(doc => 
            vscode.commands.executeCommand(
                'vscode.executeCompletionItemProvider',
                doc.uri,
                position
            )
        );

        const results = await Promise.all(completionPromises);
        const endTime = Date.now();
        const totalTime = endTime - startTime;

        assert.strictEqual(results.length, 3);
        results.forEach(result => assert.ok(result));
        assert.ok(totalTime < 15000, `Concurrent requests took ${totalTime}ms`);
    });
});
