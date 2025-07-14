// tests/test_extension/setup.ts
import * as vscode from 'vscode';
import * as path from 'path';
import { promises as fs } from 'fs';

export class TestSetup {
    static async createTestWorkspace(): Promise<vscode.Uri> {
        const testWorkspacePath = path.join(__dirname, '..', '..', 'test-workspace');
        await fs.mkdir(testWorkspacePath, { recursive: true });
        
        // Create test Python files
        const testFiles = [
            {
                name: 'test_basic.py',
                content: `def hello_world():
    print("Hello, World!")
    return "Hello"`
            },
            {
                name: 'test_class.py',
                content: `class Calculator:
    def __init__(self):
        self.value = 0
    
    def add(self, num):
        self.value += num
        return self.value`
            },
            {
                name: 'test_complex.py',
                content: `import numpy as np
import pandas as pd

def process_data(data):
    # Process data here
    pass`
            }
        ];

        for (const file of testFiles) {
            await fs.writeFile(
                path.join(testWorkspacePath, file.name),
                file.content
            );
        }

        return vscode.Uri.file(testWorkspacePath);
    }

    static async cleanupTestWorkspace(): Promise<void> {
        const testWorkspacePath = path.join(__dirname, '..', '..', 'test-workspace');
        try {
            await fs.rmdir(testWorkspacePath, { recursive: true });
        } catch (error) {
            // Ignore cleanup errors
        }
    }
}









