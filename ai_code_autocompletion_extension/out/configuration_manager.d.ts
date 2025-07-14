export declare class ConfigurationManager {
    private static readonly CONFIG_SECTION;
    private configuration;
    constructor();
    private loadConfiguration;
    reloadConfiguration(): void;
    isEnabled(): boolean;
    setEnabled(enabled: boolean): void;
    getApiUrl(): string;
    getMaxSuggestions(language?: string): number;
    getTemperature(language?: string): number;
    getMaxContextLines(language?: string): number;
    getModel(language?: string): string;
    getTopP(language?: string): number;
    getTopK(language?: string): number;
    getRepetitionPenalty(language?: string): number;
    getContextWindow(language?: string): number;
    getCommentStyle(language?: string): string;
    getIndentStyle(language?: string): 'spaces' | 'tabs';
    getIndentSize(language?: string): number;
    getLanguageConfig(language: string): any;
    getSupportedLanguages(): string[];
    isLanguageSupported(language: string): boolean;
    getAutoTrigger(): boolean;
    getAllSettings(language?: string): Record<string, any>;
    validateConfiguration(): {
        valid: boolean;
        errors: string[];
    };
    updateLanguageConfig(language: string, config: Record<string, any>): Promise<void>;
    removeLanguageConfig(language: string): Promise<void>;
    private isValidUrl;
    resetToDefaults(): Promise<void>;
}
//# sourceMappingURL=configuration_manager.d.ts.map