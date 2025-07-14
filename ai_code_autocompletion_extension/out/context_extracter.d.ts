import * as vscode from 'vscode';
import { CodeContext } from './completion_provider';
export declare class ContextExtractor {
    private maxContextLines;
    extractContext(document: vscode.TextDocument, position: vscode.Position): CodeContext;
    private getPreviousLines;
    private extractFunctionContext;
    private extractClassContext;
    private extractClassMembers;
    private extractImports;
    private extractVariables;
    private parseParameters;
    private inferType;
}
//# sourceMappingURL=context_extracter.d.ts.map