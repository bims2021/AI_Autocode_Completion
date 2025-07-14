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
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const completion_provider_1 = require("./completion_provider");
const configuration_manager_1 = require("./configuration_manager");
const api_client_1 = require("./api_client");
const context_extracter_1 = require("./context_extracter");
const ui_handler_1 = require("./ui_handler");
const statistics_manager_1 = require("./statistics_manager");
let completionProvider;
let configManager;
let apiClient;
let contextExtractor;
let uiHandler;
let statsManager;
function activate(context) {
    console.log('Extension activation started...');
    // Add this line to also show in VS Code's output
    vscode.window.showInformationMessage('AI Code Autocompletion extension is now active');
    console.log('AI Code Autocompletion extension is now active');
    ;
    // Initialize components
    configManager = new configuration_manager_1.ConfigurationManager();
    apiClient = new api_client_1.APIClient(configManager);
    contextExtractor = new context_extracter_1.ContextExtractor();
    uiHandler = new ui_handler_1.UIHandler(context);
    statsManager = new statistics_manager_1.StatisticsManager(context);
    completionProvider = new completion_provider_1.CompletionProvider(apiClient, contextExtractor, configManager, statsManager);
    // Register completion providers for supported languages
    const supportedLanguages = ['python', 'javascript', 'typescript', 'java', 'go', 'rust'];
    supportedLanguages.forEach(language => {
        const provider = vscode.languages.registerCompletionItemProvider(language, completionProvider, 
        // Trigger characters
        '.', '(', '[', '{', ' ', '\n');
        context.subscriptions.push(provider);
    });
    // Register commands
    const toggleCommand = vscode.commands.registerCommand('aiCodeCompletion.toggle', () => {
        const enabled = configManager.isEnabled();
        configManager.setEnabled(!enabled);
        uiHandler.showMessage(`AI Code Completion ${!enabled ? 'enabled' : 'disabled'}`, 'info');
    });
    const clearCacheCommand = vscode.commands.registerCommand('aiCodeCompletion.clearCache', () => {
        apiClient.clearCache();
        uiHandler.showMessage('Completion cache cleared', 'info');
    });
    const showStatsCommand = vscode.commands.registerCommand('aiCodeCompletion.showStats', () => {
        statsManager.showStatistics();
    });
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
exports.activate = activate;
function deactivate() {
    console.log('AI Code Autocompletion extension is being deactivated');
    if (statsManager) {
        statsManager.saveStatistics();
    }
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map