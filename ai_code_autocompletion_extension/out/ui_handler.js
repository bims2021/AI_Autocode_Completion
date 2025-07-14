"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.UIHandler = void 0;
const vscode = __importStar(require("vscode"));
class UIHandler {
    constructor(context) {
        this.context = context;
        this.setupStatusBar();
        this.setupOutputChannel();
    }
    setupStatusBar() {
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.text = "$(robot) AI Completion";
        this.statusBarItem.tooltip = "AI Code Autocompletion - Click to toggle";
        this.statusBarItem.command = 'aiCodeCompletion.toggle';
        this.statusBarItem.show();
        this.context.subscriptions.push(this.statusBarItem);
    }
    setupOutputChannel() {
        this.outputChannel = vscode.window.createOutputChannel('AI Code Completion');
        this.context.subscriptions.push(this.outputChannel);
    }
    showMessage(message, type = 'info') {
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
    logMessage(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logLevel = type.toUpperCase();
        this.outputChannel.appendLine(`[${timestamp}] ${logLevel}: ${message}`);
    }
    updateStatusBar(text, tooltip) {
        this.statusBarItem.text = text;
        if (tooltip) {
            this.statusBarItem.tooltip = tooltip;
        }
    }
    setStatusBarEnabled(enabled) {
        if (enabled) {
            this.statusBarItem.text = "$(robot) AI Completion";
            this.statusBarItem.backgroundColor = undefined;
            this.statusBarItem.tooltip = "AI Code Autocompletion is enabled - Click to toggle";
        }
        else {
            this.statusBarItem.text = "$(robot) AI Disabled";
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            this.statusBarItem.tooltip = "AI Code Autocompletion is disabled - Click to toggle";
        }
    }
    async showConfigurationDialog() {
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
    async showApiConnectionError(apiUrl) {
        const action = await vscode.window.showErrorMessage(`Cannot connect to AI service at ${apiUrl}. Please check your configuration.`, 'Open Settings', 'Retry', 'Disable Extension');
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
    async showFirstTimeSetup() {
        const setup = await vscode.window.showInformationMessage('Welcome to AI Code Autocompletion! Would you like to configure the extension?', 'Configure Now', 'Use Defaults', 'Learn More');
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
    showProgress(title, task) {
        return Promise.resolve(vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title,
            cancellable: false
        }, task));
    }
    async showQuickPick(items, options) {
        return await vscode.window.showQuickPick(items, options);
    }
    async showInputBox(options) {
        return await vscode.window.showInputBox(options);
    }
    dispose() {
        this.statusBarItem.dispose();
        this.outputChannel.dispose();
    }
}
exports.UIHandler = UIHandler;
//# sourceMappingURL=ui_handler.js.map