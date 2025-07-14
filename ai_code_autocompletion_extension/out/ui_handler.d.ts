import * as vscode from 'vscode';
export type MessageType = 'info' | 'warning' | 'error';
export declare class UIHandler {
    private context;
    private statusBarItem;
    private outputChannel;
    constructor(context: vscode.ExtensionContext);
    private setupStatusBar;
    private setupOutputChannel;
    showMessage(message: string, type?: MessageType): void;
    logMessage(message: string, type?: MessageType): void;
    updateStatusBar(text: string, tooltip?: string): void;
    setStatusBarEnabled(enabled: boolean): void;
    showConfigurationDialog(): Promise<void>;
    showApiConnectionError(apiUrl: string): Promise<boolean>;
    showFirstTimeSetup(): Promise<void>;
    showProgress<T>(title: string, task: (progress: vscode.Progress<{
        message?: string;
        increment?: number;
    }>) => Promise<T>): Promise<T>;
    showQuickPick<T extends vscode.QuickPickItem>(items: T[], options: vscode.QuickPickOptions): Promise<T | undefined>;
    showInputBox(options: vscode.InputBoxOptions): Promise<string | undefined>;
    dispose(): void;
}
//# sourceMappingURL=ui_handler.d.ts.map