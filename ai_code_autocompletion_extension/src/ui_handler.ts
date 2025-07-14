import * as vscode from 'vscode';

export type MessageType = 'info' | 'warning' | 'error';

export class UIHandler {
    private statusBarItem!: vscode.StatusBarItem;
    private outputChannel!: vscode.OutputChannel;

    constructor(private context: vscode.ExtensionContext) {
        this.setupStatusBar();
        this.setupOutputChannel();
    }

    private setupStatusBar(): void {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        this.statusBarItem.text = "$(robot) AI Completion";
        this.statusBarItem.tooltip = "AI Code Autocompletion - Click to toggle";
        this.statusBarItem.command = 'aiCodeCompletion.toggle';
        this.statusBarItem.show();
        
        this.context.subscriptions.push(this.statusBarItem);
    }

    private setupOutputChannel(): void {
        this.outputChannel = vscode.window.createOutputChannel('AI Code Completion');
        this.context.subscriptions.push(this.outputChannel);
    }

    public showMessage(message: string, type: MessageType = 'info'): void {
        switch (type) {
            case 'info':
                vscode.window.showInformationMessage(`AI Completion: ${message}`);
                break;
            case 'warning':
                vscode.window.showWarningMessage(`AI Completion: ${message}`);
                break;
            case 'error':
                vscode.window.showErrorMessage(`AI Completion: ${message}`);
                break;
        }
        
        this.logMessage(message, type);
    }

    public logMessage(message: string, type: MessageType = 'info'): void {
        const timestamp = new Date().toLocaleTimeString();
        const logLevel = type.toUpperCase();
        this.outputChannel.appendLine(`[${timestamp}] ${logLevel}: ${message}`);
    }

    public updateStatusBar(text: string, tooltip?: string): void {
        this.statusBarItem.text = text;
        if (tooltip) {
            this.statusBarItem.tooltip = tooltip;
        }
    }

    public setStatusBarEnabled(enabled: boolean): void {
        if (enabled) {
            this.statusBarItem.text = "$(robot) AI Completion";
            this.statusBarItem.backgroundColor = undefined;
            this.statusBarItem.tooltip = "AI Code Autocompletion is enabled - Click to toggle";
        } else {
            this.statusBarItem.text = "$(robot) AI Disabled";
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            this.statusBarItem.tooltip = "AI Code Autocompletion is disabled - Click to toggle";
        }
    }

    public async showConfigurationDialog(): Promise<void> {
        const action = await vscode.window.showQuickPick([
            {
                label: '$(gear) Open Settings',
                description: 'Configure AI Code Completion settings'
            },
            {
                label: '$(output) Show Output',
                description: 'View extension logs and debug information'
            },
            {
                label: '$(graph) Show Statistics',
                description: 'View completion statistics and performance'
            },
            {
                label: '$(trash) Clear Cache',
                description: 'Clear completion cache'
            }
        ], {
            placeHolder: 'AI Code Completion Options'
        });

        if (!action) {
            return;
        }

        switch (action.label) {
            case '$(gear) Open Settings':
                await vscode.commands.executeCommand('workbench.action.openSettings', 'aiCodeCompletion');
                break;
            case '$(output) Show Output':
                this.outputChannel.show();
                break;
            case '$(graph) Show Statistics':
                await vscode.commands.executeCommand('aiCodeCompletion.showStats');
                break;
            case '$(trash) Clear Cache':
                await vscode.commands.executeCommand('aiCodeCompletion.clearCache');
                break;
        }
    }

    public async showApiConnectionError(apiUrl: string): Promise<boolean> {
        const action = await vscode.window.showErrorMessage(
            `Cannot connect to AI service at ${apiUrl}. Please check your configuration.`,
            'Open Settings',
            'Retry',
            'Disable Extension'
        );

        switch (action) {
            case 'Open Settings':
                await vscode.commands.executeCommand('workbench.action.openSettings', 'aiCodeCompletion.apiUrl');
                return false;
            case 'Retry':
                return true;
            case 'Disable Extension':
                await vscode.commands.executeCommand('aiCodeCompletion.toggle');
                return false;
            default:
                return false;
        }
    }

    public async showFirstTimeSetup(): Promise<void> {
        const setup = await vscode.window.showInformationMessage(
            'Welcome to AI Code Autocompletion! Would you like to configure the extension?',
            'Configure Now',
            'Use Defaults',
            'Learn More'
        );

        switch (setup) {
            case 'Configure Now':
                await this.showConfigurationDialog();
                break;
            case 'Learn More':
                await vscode.env.openExternal(vscode.Uri.parse('https://github.com/your-repo/ai-code-completion'));
                break;
            // 'Use Defaults' - do nothing, extension will use default settings
        }
    }

    public showProgress<T>(
        title: string,
        task: (progress: vscode.Progress<{ message?: string; increment?: number }>) => Promise<T>
    ): Promise<T> {
        return Promise.resolve(vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title,
                cancellable: false
            },
            task
        ));
    }

    public async showQuickPick<T extends vscode.QuickPickItem>(
        items: T[],
        options: vscode.QuickPickOptions
    ): Promise<T | undefined> {
        return await vscode.window.showQuickPick(items, options);
    }

    public async showInputBox(options: vscode.InputBoxOptions): Promise<string | undefined> {
        return await vscode.window.showInputBox(options);
    }

    public dispose(): void {
        this.statusBarItem.dispose();
        this.outputChannel.dispose();
    }
}