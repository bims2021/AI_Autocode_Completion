import * as vscode from 'vscode';
import { APIClient } from './api_client';
import * as crypto from 'crypto';
import { ContextExtractor } from './context_extracter';
import { ConfigurationManager } from './configuration_manager';
import { StatisticsManager } from './statistics_manager';

export interface CodeContext {
    currentLine: string;
    filePath?: string;
    previousLines: string[];
    position: {
        line: number;
        character: number;
    };
    language: string;
    functionContext: {
        name: string;
        parameters: string[];
        returnType?: string;
    } | null;
    classContext: {
        name: string;
        methods: string[];
        properties: string[];
    } | null;
    imports: string[];
    variables: {
        name: string;
        type: string;
        scope: 'local' | 'global' | 'parameter';
    }[];
    // New fields for enhanced language support
    fileExtension?: string;
    indentStyle?: 'spaces' | 'tabs';
    indentSize?: number;
    contextWindow?: number;
}

export interface Suggestion {
    text: string;
    confidence: number;
    type: 'single-line' | 'multi-line' | 'block';
    description?: string;
    cursorOffset: number;
    replaceRange?: {
        start: number;
        end: number;
    };
    // New fields for enhanced suggestions
    languageSpecific?: boolean;
    formattingApplied?: boolean;
}

export interface SuggestionResponse {
    suggestions: Suggestion[];
    metadata: {
        processingTimeMs: number;
        modelVersion: string;
        cacheHit: boolean;
        contextHash: string;
        // New metadata fields
        languageDetected?: string;
        configUsed?: string;
        modelType?: 'codegpt' | 'codebert';
    };
    status: 'success' | 'partial' | 'error';
    errorMessage?: string;
}

export interface LanguageConfig {
    maxTokens: number;
    temperature: number;
    topP: number;
    contextWindow: number;
    commentStyle: string;
    indentStyle: 'spaces' | 'tabs';
    indentSize: number;
    fileExtensions: string[];
}

export class CompletionProvider implements vscode.CompletionItemProvider {
    private cache = new Map<string, SuggestionResponse>();
    private isProcessing = false;
    private languageConfigs = new Map<string, LanguageConfig>();

    constructor(
        private apiClient: APIClient,
        private contextExtractor: ContextExtractor,
        private configManager: ConfigurationManager,
        private statsManager: StatisticsManager
    ) {
        this.initializeLanguageConfigs();
    }

    private initializeLanguageConfigs(): void {
        // Initialize with default language configurations
        // These should match the backend configuration
        const defaultConfigs: Record<string, LanguageConfig> = {
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

    async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[]> {
        
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
            const codeContext = this.enhanceContextWithLanguageInfo(
                this.contextExtractor.extractContext(document, position),
                document
            );

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
                this.statsManager.recordCompletion(
                    codeContext.language,
                    response.suggestions.length,
                    processingTime,
                    response.metadata.cacheHit
                );

                return this.convertToCompletionItems(response.suggestions, codeContext);
            } else {
                console.error('API Error:', response.errorMessage);
                this.statsManager.recordError('api_error');
                return [];
            }

        } catch (error) {
            console.error('Completion provider error:', error);
            this.statsManager.recordError('provider_error');
            return [];
        } finally {
            this.isProcessing = false;
        }
    }

    private enhanceContextWithLanguageInfo(context: CodeContext, document: vscode.TextDocument): CodeContext {
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

    private isLanguageSupported(language: string): boolean {
        return this.languageConfigs.has(language);
    }

    private convertToCompletionItems(suggestions: Suggestion[], context: CodeContext): vscode.CompletionItem[] {
        const languageConfig = this.languageConfigs.get(context.language);
        
        return suggestions.map((suggestion, index) => {
            const item = new vscode.CompletionItem(
                suggestion.text,
                this.getCompletionItemKind(suggestion.type)
            );

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
                const range = new vscode.Range(
                    new vscode.Position(0, suggestion.replaceRange.start),
                    new vscode.Position(0, suggestion.replaceRange.end)
                );
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

    private formatSuggestionText(text: string, context: CodeContext, config?: LanguageConfig): string {
        if (!config) return text;

        // Apply language-specific indentation
        const lines = text.split('\n');
        if (lines.length > 1) {
            const indentChar = config.indentStyle === 'tabs' ? '\t' : ' '.repeat(config.indentSize);
            return lines.map((line, index) => {
                if (index === 0) return line; // First line keeps original indentation
                return line.replace(/^(\s*)/, indentChar);
            }).join('\n');
        }

        return text;
    }

    private enhanceDescription(description: string, context: CodeContext): string {
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

    private getCompletionItemKind(suggestionType: string): vscode.CompletionItemKind {
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

    private generateContextHash(context: CodeContext): string {
        const contextString = JSON.stringify({
            currentLine: context.currentLine,
            previousLines: context.previousLines.slice(-10), // Last 10 lines for hash
            language: context.language,
            functionContext: context.functionContext,
            classContext: context.classContext,
            fileExtension: context.fileExtension,
            indentStyle: context.indentStyle,
            indentSize: context.indentSize
        });
        return crypto.createHash('md5').update(contextString).digest('hex');
    }

    private cleanupCache(): void {
        // Keep cache size reasonable (max 100 entries)
        if (this.cache.size > 100) {
            const keysToDelete = Array.from(this.cache.keys()).slice(0, 50);
            keysToDelete.forEach(key => this.cache.delete(key));
        }
    }

    public clearCache(): void {
        this.cache.clear();
    }

    // New method to update language configurations
    public updateLanguageConfig(language: string, config: Partial<LanguageConfig>): void {
        const existingConfig = this.languageConfigs.get(language);
        if (existingConfig) {
            this.languageConfigs.set(language, { ...existingConfig, ...config });
        } else {
            // Add new language configuration
            const defaultConfig: LanguageConfig = {
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
    public getSupportedLanguages(): string[] {
        return Array.from(this.languageConfigs.keys());
    }

    // New method to get language configuration
    public getLanguageConfig(language: string): LanguageConfig | undefined {
        return this.languageConfigs.get(language);
    }
}