import * as vscode from 'vscode';
import { CompletionProvider } from './completion_provider';
import { ConfigurationManager } from './configuration_manager';
import { APIClient } from './api_client';
import { ContextExtractor } from './context_extracter';
import { UIHandler } from './ui_handler';
import { StatisticsManager } from './statistics_manager';

let completionProvider: CompletionProvider;
let configManager: ConfigurationManager;
let apiClient: APIClient;
let contextExtractor: ContextExtractor;
let uiHandler: UIHandler;
let statsManager: StatisticsManager;

export function activate(context: vscode.ExtensionContext) {
    console.log('Extension activation started...');
    
    // Add this line to also show in VS Code's output
    vscode.window.showInformationMessage('AI Code Autocompletion extension is now active');
    
    console.log('AI Code Autocompletion extension is now active');
    ;

    // Initialize components
    configManager = new ConfigurationManager();
    apiClient = new APIClient(configManager);
    contextExtractor = new ContextExtractor();
    uiHandler = new UIHandler(context);
    statsManager = new StatisticsManager(context);
    completionProvider = new CompletionProvider(
        apiClient,
        contextExtractor,
        configManager,
        statsManager
    );

    // Register completion providers for supported languages
    const supportedLanguages = ['python', 'javascript', 'typescript', 'java', 'go', 'rust'];
    
    supportedLanguages.forEach(language => {
        const provider = vscode.languages.registerCompletionItemProvider(
            language,
            completionProvider,
            // Trigger characters
            '.', '(', '[', '{', ' ', '\n'
        );
        context.subscriptions.push(provider);
    });

    // Register commands
    const toggleCommand = vscode.commands.registerCommand(
        'aiCodeCompletion.toggle',
        () => {
            const enabled = configManager.isEnabled();
            configManager.setEnabled(!enabled);
            uiHandler.showMessage(
                `AI Code Completion ${!enabled ? 'enabled' : 'disabled'}`,
                'info'
            );
        }
    );

    const clearCacheCommand = vscode.commands.registerCommand(
        'aiCodeCompletion.clearCache',
        () => {
            apiClient.clearCache();
            uiHandler.showMessage('Completion cache cleared', 'info');
        }
    );

    const showStatsCommand = vscode.commands.registerCommand(
        'aiCodeCompletion.showStats',
        () => {
            statsManager.showStatistics();
        }
    );

    context.subscriptions.push(toggleCommand, clearCacheCommand, showStatsCommand);

    // Listen for configuration changes
    const configChangeListener = vscode.workspace.onDidChangeConfiguration(event => {
        if (event.affectsConfiguration('aiCodeCompletion')) {
            configManager.reloadConfiguration();
            apiClient.updateConfiguration(configManager);
        }
    });

    context.subscriptions.push(configChangeListener);

    // Show welcome message
    uiHandler.showMessage('AI Code Autocompletion activated!', 'info');
}

export function deactivate() {
    console.log('AI Code Autocompletion extension is being deactivated');
    if (statsManager) {
        statsManager.saveStatistics();
    }
}