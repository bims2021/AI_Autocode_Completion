import { ConfigurationManager } from './configuration_manager';
import { CodeContext, SuggestionResponse } from './completion_provider';
export interface CompletionRequest {
    context: CodeContext;
    language: string;
    max_suggestions: number;
    max_length: number;
    temperature: number;
    user_id?: string;
    session_id?: string;
    preferences?: Record<string, any>;
}
export declare class APIClient {
    private configManager;
    private httpClient;
    private userId;
    private sessionId;
    private requestTimeout;
    constructor(configManager: ConfigurationManager);
    private initializeHttpClient;
    getSuggestions(context: CodeContext): Promise<SuggestionResponse>;
    sendFeedback(suggestionIndex: number, accepted: boolean, context: CodeContext): Promise<void>;
    checkHealth(): Promise<boolean>;
    getModelInfo(): Promise<{
        models: string[];
        current: string;
        supportedLanguages: string[];
    } | null>;
    getLanguageConfig(language: string): Promise<any | null>;
    updateConfiguration(configManager: ConfigurationManager): void;
    clearCache(): void;
    clearLanguageCache(language: string): void;
    private detectLanguage;
    private getMaxLength;
    private isValidSuggestionResponse;
    private getErrorMessage;
    private generateUserId;
    private generateSessionId;
    private generateContextHash;
}
//# sourceMappingURL=api_client.d.ts.map