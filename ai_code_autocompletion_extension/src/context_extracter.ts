import * as vscode from 'vscode';
import { CodeContext } from './completion_provider';

export class ContextExtractor {
    private maxContextLines = 50;

    extractContext(document: vscode.TextDocument, position: vscode.Position): CodeContext {
        const language = document.languageId;
        const currentLine = document.lineAt(position.line).text;
        const previousLines = this.getPreviousLines(document, position.line);

        // Extract various context elements
        const functionContext = this.extractFunctionContext(document, position);
        const classContext = this.extractClassContext(document, position);
        const imports = this.extractImports(document);
        const variables = this.extractVariables(document, position);

        return {
            currentLine: currentLine.substring(0, position.character),
            previousLines,
            position: {
                line: position.line,
                character: position.character
            },
            language,
            functionContext,
            classContext,
            imports,
            variables
        };
    }

    private getPreviousLines(document: vscode.TextDocument, currentLine: number): string[] {
        const startLine = Math.max(0, currentLine - this.maxContextLines);
        const lines: string[] = [];

        for (let i = startLine; i < currentLine; i++) {
            lines.push(document.lineAt(i).text);
        }

        return lines;
    }

    private extractFunctionContext(document: vscode.TextDocument, position: vscode.Position): {
        name: string;
        parameters: string[];
        returnType?: string;
    } | null {
        // Look backwards to find function definition
        for (let i = position.line; i >= 0; i--) {
            const line = document.lineAt(i).text.trim();
            
            // Python function pattern
            const pythonMatch = line.match(/^def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:/);
            if (pythonMatch) {
                return {
                    name: pythonMatch[1],
                    parameters: this.parseParameters(pythonMatch[2]),
                    returnType: pythonMatch[3]?.trim()
                };
            }

            // JavaScript/TypeScript function pattern
            const jsMatch = line.match(/(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?/);
            if (jsMatch) {
                return {
                    name: jsMatch[1] || jsMatch[2],
                    parameters: this.parseParameters(jsMatch[3]),
                    returnType: jsMatch[4]?.trim()
                };
            }

            // Java method pattern
            const javaMatch = line.match(/(?:public|private|protected)?\s*(?:static)?\s*(?:\w+\s+)*(\w+)\s*\(([^)]*)\)/);
            if (javaMatch) {
                return {
                    name: javaMatch[1],
                    parameters: this.parseParameters(javaMatch[2])
                };
            }
        }

        return null;
    }

    private extractClassContext(document: vscode.TextDocument, position: vscode.Position): {
        name: string;
        methods: string[];
        properties: string[];
    } | null {
        let className: string | null = null;
        const methods: string[] = [];
        const properties: string[] = [];

        // Look backwards to find class definition
        for (let i = position.line; i >= 0; i--) {
            const line = document.lineAt(i).text.trim();
            
            // Python class pattern
            const pythonClassMatch = line.match(/^class\s+(\w+)(?:\([^)]*\))?:/);
            if (pythonClassMatch) {
                className = pythonClassMatch[1];
                break;
            }

            // JavaScript/TypeScript class pattern
            const jsClassMatch = line.match(/^(?:export\s+)?class\s+(\w+)/);
            if (jsClassMatch) {
                className = jsClassMatch[1];
                break;
            }

            // Java class pattern
            const javaClassMatch = line.match(/(?:public|private|protected)?\s*class\s+(\w+)/);
            if (javaClassMatch) {
                className = javaClassMatch[1];
                break;
            }
        }

        if (className) {
            // Extract methods and properties within the class
            this.extractClassMembers(document, position, methods, properties);
        }

        return className ? { name: className, methods, properties } : null;
    }

    private extractClassMembers(
        document: vscode.TextDocument,
        position: vscode.Position,
        methods: string[],
        properties: string[]
    ): void {
        const totalLines = document.lineCount;
        
        for (let i = 0; i < totalLines; i++) {
            const line = document.lineAt(i).text.trim();
            
            // Extract method names
            const methodMatch = line.match(/(?:def\s+(\w+)|(\w+)\s*\([^)]*\)\s*[{:]|(?:public|private|protected)\s+(?:\w+\s+)*(\w+)\s*\([^)]*\))/);
            if (methodMatch) {
                const methodName = methodMatch[1] || methodMatch[2] || methodMatch[3];
                if (methodName && !methods.includes(methodName)) {
                    methods.push(methodName);
                }
            }

            // Extract property names (simplified)
            const propertyMatch = line.match(/(?:self\.(\w+)|this\.(\w+)|private\s+(\w+)|public\s+(\w+))/);
            if (propertyMatch) {
                const propertyName = propertyMatch[1] || propertyMatch[2] || propertyMatch[3] || propertyMatch[4];
                if (propertyName && !properties.includes(propertyName)) {
                    properties.push(propertyName);
                }
            }
        }
    }

    private extractImports(document: vscode.TextDocument): string[] {
        const imports: string[] = [];
        const totalLines = Math.min(50, document.lineCount); // Check first 50 lines

        for (let i = 0; i < totalLines; i++) {
            const line = document.lineAt(i).text.trim();
            
            // Python imports
            if (line.match(/^(?:import|from)\s+/)) {
                imports.push(line);
            }
            
            // JavaScript/TypeScript imports
            if (line.match(/^import\s+/)) {
                imports.push(line);
            }
            
            // Java imports
            if (line.match(/^import\s+/)) {
                imports.push(line);
            }
        }

        return imports;
    }

    private extractVariables(document: vscode.TextDocument, position: vscode.Position): {
        name: string;
        type: string;
        scope: 'local' | 'global' | 'parameter';
    }[] {
        const variables: Array<{name: string; type: string; scope: 'local' | 'global' | 'parameter'}> = [];
        
        // Look at current function scope for local variables
        for (let i = Math.max(0, position.line - 20); i < position.line; i++) {
            const line = document.lineAt(i).text.trim();
            
            // Python variable declarations
            const pythonVarMatch = line.match(/(\w+)\s*=\s*(.+)/);
            if (pythonVarMatch) {
                variables.push({
                    name: pythonVarMatch[1],
                    type: this.inferType(pythonVarMatch[2]),
                    scope: 'local'
                });
            }
            
            // JavaScript/TypeScript variable declarations
            const jsVarMatch = line.match(/(?:const|let|var)\s+(\w+)(?:\s*:\s*(\w+))?\s*=\s*(.+)/);
            if (jsVarMatch) {
                variables.push({
                    name: jsVarMatch[1],
                    type: jsVarMatch[2] || this.inferType(jsVarMatch[3]),
                    scope: 'local'
                });
            }
        }

        return variables;
    }

    private parseParameters(paramString: string): string[] {
        if (!paramString.trim()) {
            return [];
        }
        
        return paramString.split(',').map(param => param.trim().split(/[:\s]/)[0]).filter(p => p);
    }

    private inferType(value: string): string {
        value = value.trim();
        
        if (value.match(/^["']/)) {
            return 'string';
        }
        if (value.match(/^\d+$/)) {
            return 'number';
        }
        if (value.match(/^(true|false)$/)) {
            return 'boolean';
        }
        if (value.match(/^\[/)) {
            return 'array';
        }
        if (value.match(/^\{/)) {
            return 'object';
        }
        
        return 'unknown';
    }
}