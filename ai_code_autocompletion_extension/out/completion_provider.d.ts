import * as vscode from 'vscode';
import { APIClient } from './api_client';
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
export declare class CompletionProvider implements vscode.CompletionItemProvider {
    private apiClient;
    private contextExtractor;
    private configManager;
    private statsManager;
    private cache;
    private isProcessing;
    private languageConfigs;
    constructor(apiClient: APIClient, contextExtractor: ContextExtractor, configManager: ConfigurationManager, statsManager: StatisticsManager);
    private initializeLanguageConfigs;
    provideCompletionItems(document: vscode.TextDocument, position: vscode.Position, token: vscode.CancellationToken, context: vscode.CompletionContext): Promise<vscode.CompletionItem[]>;
    private enhanceContextWithLanguageInfo;
    private isLanguageSupported;
    private convertToCompletionItems;
    private formatSuggestionText;
    private enhanceDescription;
    private getCompletionItemKind;
    private generateContextHash;
    private cleanupCache;
    clearCache(): void;
    updateLanguageConfig(language: string, config: Partial<LanguageConfig>): void;
    getSupportedLanguages(): string[];
    getLanguageConfig(language: string): LanguageConfig | undefined;
}
//# sourceMappingURL=completion_provider.d.ts.map