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
exports.CompletionProvider = void 0;
const vscode = __importStar(require("vscode"));
const crypto = __importStar(require("crypto"));
class CompletionProvider {
    constructor(apiClient, contextExtractor, configManager, statsManager) {
        this.apiClient = apiClient;
        this.contextExtractor = contextExtractor;
        this.configManager = configManager;
        this.statsManager = statsManager;
        this.cache = new Map();
        this.isProcessing = false;
        this.languageConfigs = new Map();
        this.initializeLanguageConfigs();
    }
    initializeLanguageConfigs() {
        // Initialize with default language configurations
        // These should match the backend configuration
        const defaultConfigs = {
            'python': {
                maxTokens: 150,
                temperature: 0.6,
                topP: 0.85,
                contextWindow: 2048,
                commentStyle: '#',
                indentStyle: 'spaces',
                indentSize: 4,
                fileExtensions: ['.py', '.pyx', '.pyi']
            },
            'javascript': {
                maxTokens: 120,
                temperature: 0.7,
                topP: 0.9,
                contextWindow: 1536,
                commentStyle: '//',
                indentStyle: 'spaces',
                indentSize: 2,
                fileExtensions: ['.js', '.jsx', '.mjs']
            },
            'typescript': {
                maxTokens: 120,
                temperature: 0.7,
                topP: 0.9,
                contextWindow: 1536,
                commentStyle: '//',
                indentStyle: 'spaces',
                indentSize: 2,
                fileExtensions: ['.ts', '.tsx']
            },
            'java': {
                maxTokens: 140,
                temperature: 0.6,
                topP: 0.85,
                contextWindow: 1800,
                commentStyle: '//',
                indentStyle: 'spaces',
                indentSize: 4,
                fileExtensions: ['.java']
            },
            'cpp': {
                maxTokens: 130,
                temperature: 0.6,
                topP: 0.85,
                contextWindow: 1800,
                commentStyle: '//',
                indentStyle: 'spaces',
                indentSize: 4,
                fileExtensions: ['.cpp', '.cc', '.cxx', '.c++']
            },
            'c': {
                maxTokens: 130,
                temperature: 0.6,
                topP: 0.85,
                contextWindow: 1800,
                commentStyle: '//',
                indentStyle: 'spaces',
                indentSize: 4,
                fileExtensions: ['.c', '.h']
            },
            'go': {
                maxTokens: 120,
                temperature: 0.6,
                topP: 0.85,
                contextWindow: 1600,
                commentStyle: '//',
                indentStyle: 'tabs',
                indentSize: 1,
                fileExtensions: ['.go']
            },
            'rust': {
                maxTokens: 140,
                temperature: 0.6,
                topP: 0.85,
                contextWindow: 1800,
                commentStyle: '//',
                indentStyle: 'spaces',
                indentSize: 4,
                fileExtensions: ['.rs']
            }
        };
        Object.entries(defaultConfigs).forEach(([lang, config]) => {
            this.languageConfigs.set(lang, config);
        });
    }
    async provideCompletionItems(document, position, token, context) {
        // Check if extension is enabled
        if (!this.configManager.isEnabled()) {
            return [];
        }
        // Avoid multiple simultaneous requests
        if (this.isProcessing) {
            return [];
        }
        try {
            this.isProcessing = true;
            const startTime = Date.now();
            // Extract context from current document with enhanced language detection
            const codeContext = this.enhanceContextWithLanguageInfo(this.contextExtractor.extractContext(document, position), document);
            // Validate language support
            if (!this.isLanguageSupported(codeContext.language)) {
                console.warn(`Language ${codeContext.language} not supported`);
                return [];
            }
            const contextHash = this.generateContextHash(codeContext);
            // Check cache first
            const cachedResponse = this.cache.get(contextHash);
            if (cachedResponse && cachedResponse.status === 'success') {
                this.statsManager.recordCacheHit();
                return this.convertToCompletionItems(cachedResponse.suggestions, codeContext);
            }
            // Make API request for suggestions with language-specific parameters
            const response = await this.apiClient.getSuggestions(codeContext);
            if (response.status === 'success') {
                // Cache successful responses
                this.cache.set(contextHash, response);
                this.cleanupCache();
                // Record statistics with language information
                const processingTime = Date.now() - startTime;
                this.statsManager.recordCompletion(codeContext.language, response.suggestions.length, processingTime, response.metadata.cacheHit);
                return this.convertToCompletionItems(response.suggestions, codeContext);
            }
            else {
                console.error('API Error:', response.errorMessage);
                this.statsManager.recordError('api_error');
                return [];
            }
        }
        catch (error) {
            console.error('Completion provider error:', error);
            this.statsManager.recordError('provider_error');
            return [];
        }
        finally {
            this.isProcessing = false;
        }
    }
    enhanceContextWithLanguageInfo(context, document) {
        const language = document.languageId;
        const fileExtension = document.fileName.split('.').pop();
        const languageConfig = this.languageConfigs.get(language);
        return {
            ...context,
            language,
            fileExtension: fileExtension ? `.${fileExtension}` : undefined,
            indentStyle: languageConfig?.indentStyle || 'spaces',
            indentSize: languageConfig?.indentSize || 4,
            contextWindow: languageConfig?.contextWindow || 1024
        };
    }
    isLanguageSupported(language) {
        return this.languageConfigs.has(language);
    }
    convertToCompletionItems(suggestions, context) {
        const languageConfig = this.languageConfigs.get(context.language);
        return suggestions.map((suggestion, index) => {
            const item = new vscode.CompletionItem(suggestion.text, this.getCompletionItemKind(suggestion.type));
            // Apply language-specific formatting to insert text
            item.insertText = this.formatSuggestionText(suggestion.text, context, languageConfig);
            // Enhanced detail with language and confidence info
            item.detail = `AI Suggestion (${Math.round(suggestion.confidence * 100)}% confidence) - ${context.language}`;
            // Add description with language-specific context
            if (suggestion.description) {
                const enhancedDescription = this.enhanceDescription(suggestion.description, context);
                item.documentation = new vscode.MarkdownString(enhancedDescription);
            }
            // Set sort priority based on confidence and language specificity
            const priorityBonus = suggestion.languageSpecific ? 100 : 0;
            const sortValue = 1000 - Math.round(suggestion.confidence * 999) - priorityBonus;
            item.sortText = String(sortValue).padStart(4, '0');
            // Handle replace range if specified
            if (suggestion.replaceRange) {
                const range = new vscode.Range(new vscode.Position(0, suggestion.replaceRange.start), new vscode.Position(0, suggestion.replaceRange.end));
                item.range = range;
            }
            // Add command to track acceptance with language info
            item.command = {
                command: 'aiCodeCompletion.trackAcceptance',
                title: 'Track Acceptance',
                arguments: [index, suggestion.type, context.language]
            };
            return item;
        });
    }
    formatSuggestionText(text, context, config) {
        if (!config)
            return text;
        // Apply language-specific indentation
        const lines = text.split('\n');
        if (lines.length > 1) {
            const indentChar = config.indentStyle === 'tabs' ? '\t' : ' '.repeat(config.indentSize);
            return lines.map((line, index) => {
                if (index === 0)
                    return line; // First line keeps original indentation
                return line.replace(/^(\s*)/, indentChar);
            }).join('\n');
        }
        return text;
    }
    enhanceDescription(description, context) {
        const languageConfig = this.languageConfigs.get(context.language);
        let enhanced = description;
        // Add language-specific context
        if (languageConfig) {
            enhanced += `\n\n**Language:** ${context.language}`;
            enhanced += `\n**Indent Style:** ${languageConfig.indentStyle} (${languageConfig.indentSize})`;
            enhanced += `\n**Comment Style:** ${languageConfig.commentStyle}`;
        }
        return enhanced;
    }
    getCompletionItemKind(suggestionType) {
        switch (suggestionType) {
            case 'single-line':
                return vscode.CompletionItemKind.Text;
            case 'multi-line':
                return vscode.CompletionItemKind.Snippet;
            case 'block':
                return vscode.CompletionItemKind.Module;
            default:
                return vscode.CompletionItemKind.Text;
        }
    }
    generateContextHash(context) {
        const contextString = JSON.stringify({
            currentLine: context.currentLine,
            previousLines: context.previousLines.slice(-10),
            language: context.language,
            functionContext: context.functionContext,
            classContext: context.classContext,
            fileExtension: context.fileExtension,
            indentStyle: context.indentStyle,
            indentSize: context.indentSize
        });
        return crypto.createHash('md5').update(contextString).digest('hex');
    }
    cleanupCache() {
        // Keep cache size reasonable (max 100 entries)
        if (this.cache.size > 100) {
            const keysToDelete = Array.from(this.cache.keys()).slice(0, 50);
            keysToDelete.forEach(key => this.cache.delete(key));
        }
    }
    clearCache() {
        this.cache.clear();
    }
    // New method to update language configurations
    updateLanguageConfig(language, config) {
        const existingConfig = this.languageConfigs.get(language);
        if (existingConfig) {
            this.languageConfigs.set(language, { ...existingConfig, ...config });
        }
        else {
            // Add new language configuration
            const defaultConfig = {
                maxTokens: 100,
                temperature: 0.7,
                topP: 0.9,
                contextWindow: 1024,
                commentStyle: '//',
                indentStyle: 'spaces',
                indentSize: 4,
                fileExtensions: []
            };
            this.languageConfigs.set(language, { ...defaultConfig, ...config });
        }
    }
    // New method to get supported languages
    getSupportedLanguages() {
        return Array.from(this.languageConfigs.keys());
    }
    // New method to get language configuration
    getLanguageConfig(language) {
        return this.languageConfigs.get(language);
    }
}
exports.CompletionProvider = CompletionProvider;
//# sourceMappingURL=completion_provider.js.map