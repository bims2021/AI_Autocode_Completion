import * as vscode from 'vscode';

export class ConfigurationManager {
    private static readonly CONFIG_SECTION = 'aiCodeCompletion';
    private configuration!: vscode.WorkspaceConfiguration;

    constructor() {
        this.loadConfiguration();
    }

    private loadConfiguration(): void {
        this.configuration = vscode.workspace.getConfiguration(ConfigurationManager.CONFIG_SECTION);
    }

    public reloadConfiguration(): void {
        this.loadConfiguration();
    }

    public isEnabled(): boolean {
        return this.configuration.get<boolean>('enabled', true);
    }

    public setEnabled(enabled: boolean): void {
        this.configuration.update('enabled', enabled, vscode.ConfigurationTarget.Global);
    }

    public getApiUrl(): string {
        return this.configuration.get<string>('apiUrl', 'http://localhost:8000');
    }

    // Enhanced: Get language-specific maxSuggestions with fallback chain
    public getMaxSuggestions(language?: string): number {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.maxSuggestions === 'number') {
                return langConfig.maxSuggestions;
            }
        }
        return this.configuration.get<number>('maxSuggestions', 3);
    }

    // Enhanced: Get language-specific temperature with fallback chain
    public getTemperature(language?: string): number {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.temperature === 'number') {
                return langConfig.temperature;
            }
        }
        return this.configuration.get<number>('temperature', 0.7);
    }

    // Enhanced: Get language-specific maxContextLines with fallback chain
    public getMaxContextLines(language?: string): number {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.maxContextLines === 'number') {
                return langConfig.maxContextLines;
            }
        }
        return this.configuration.get<number>('maxContextLines', 50);
    }

    // Enhanced: Get language-specific model with fallback chain
    public getModel(language?: string): string {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.model === 'string') {
                return langConfig.model;
            }
        }
        return this.configuration.get<string>('model', 'auto');
    }

    // New: Get language-specific top_p parameter
    public getTopP(language?: string): number {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.topP === 'number') {
                return langConfig.topP;
            }
        }
        return this.configuration.get<number>('topP', 0.9);
    }

    // New: Get language-specific top_k parameter
    public getTopK(language?: string): number {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.topK === 'number') {
                return langConfig.topK;
            }
        }
        return this.configuration.get<number>('topK', 50);
    }

    // New: Get language-specific repetition penalty
    public getRepetitionPenalty(language?: string): number {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.repetitionPenalty === 'number') {
                return langConfig.repetitionPenalty;
            }
        }
        return this.configuration.get<number>('repetitionPenalty', 1.1);
    }

    // New: Get language-specific context window size
    public getContextWindow(language?: string): number {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.contextWindow === 'number') {
                return langConfig.contextWindow;
            }
        }
        return this.configuration.get<number>('contextWindow', 1024);
    }

    // New: Get language-specific comment style
    public getCommentStyle(language?: string): string {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.commentStyle === 'string') {
                return langConfig.commentStyle;
            }
        }
        
        // Default comment styles for common languages
        const defaultCommentStyles: Record<string, string> = {
            'python': '#',
            'javascript': '//',
            'typescript': '//',
            'java': '//',
            'cpp': '//',
            'c': '//',
            'c#': '//',
            'go': '//',
            'rust': '//',
            'php': '//',
            'ruby': '#',
            'html': '<!-- -->',
            'css': '/* */',
            'sql': '--'
        };
        
        return language ? defaultCommentStyles[language] || '//' : '//';
    }

    // New: Get language-specific indent style
    public getIndentStyle(language?: string): 'spaces' | 'tabs' {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && (langConfig.indentStyle === 'spaces' || langConfig.indentStyle === 'tabs')) {
                return langConfig.indentStyle;
            }
        }
        
        // Default indent styles for common languages
        const defaultIndentStyles: Record<string, 'spaces' | 'tabs'> = {
            'python': 'spaces',
            'javascript': 'spaces',
            'typescript': 'spaces',
            'java': 'spaces',
            'cpp': 'spaces',
            'c': 'spaces',
            'c#': 'spaces',
            'go': 'tabs',
            'rust': 'spaces',
            'php': 'spaces',
            'ruby': 'spaces',
            'html': 'spaces',
            'css': 'spaces',
            'sql': 'spaces'
        };
        
        return language ? defaultIndentStyles[language] || 'spaces' : 'spaces';
    }

    // New: Get language-specific indent size
    public getIndentSize(language?: string): number {
        if (language) {
            const langConfig = this.getLanguageConfig(language);
            if (langConfig && typeof langConfig.indentSize === 'number') {
                return langConfig.indentSize;
            }
        }
        
        // Default indent sizes for common languages
        const defaultIndentSizes: Record<string, number> = {
            'python': 4,
            'javascript': 2,
            'typescript': 2,
            'java': 4,
            'cpp': 4,
            'c': 4,
            'c#': 4,
            'go': 1, // Go uses tabs
            'rust': 4,
            'php': 4,
            'ruby': 2,
            'html': 2,
            'css': 2,
            'sql': 2
        };
        
        return language ? defaultIndentSizes[language] || 4 : 4;
    }

    // New: Get complete language-specific configuration
    public getLanguageConfig(language: string): any {
        const languageSettings = this.configuration.get<Record<string, any>>('languages', {});
        return languageSettings[language] || {};
    }

    // New: Get all supported languages from configuration
    public getSupportedLanguages(): string[] {
        const languageSettings = this.configuration.get<Record<string, any>>('languages', {});
        const configuredLanguages = Object.keys(languageSettings);
        
        // Default supported languages
        const defaultLanguages = [
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'c#',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala',
            'html', 'css', 'sql', 'bash', 'powershell'
        ];
        
        // Combine and deduplicate
        const allLanguages = [...new Set([...defaultLanguages, ...configuredLanguages])];
        return allLanguages.sort();
    }

    // New: Check if language is supported
    public isLanguageSupported(language: string): boolean {
        return this.getSupportedLanguages().includes(language.toLowerCase());
    }

    public getAutoTrigger(): boolean {
        return this.configuration.get<boolean>('autoTrigger', true);
    }

    // Enhanced: Get all settings with optional language-specific overrides
    public getAllSettings(language?: string): Record<string, any> {
        const settings: Record<string, any> = {
            enabled: this.isEnabled(),
            apiUrl: this.getApiUrl(),
            autoTrigger: this.getAutoTrigger(),
            maxSuggestions: this.getMaxSuggestions(language),
            temperature: this.getTemperature(language),
            maxContextLines: this.getMaxContextLines(language),
            model: this.getModel(language),
            topP: this.getTopP(language),
            topK: this.getTopK(language),
            repetitionPenalty: this.getRepetitionPenalty(language),
            contextWindow: this.getContextWindow(language),
            supportedLanguages: this.getSupportedLanguages()
        };

        // Include language-specific settings if language is provided
        if (language) {
            settings.languageConfig = this.getLanguageConfig(language);
            settings.commentStyle = this.getCommentStyle(language);
            settings.indentStyle = this.getIndentStyle(language);
            settings.indentSize = this.getIndentSize(language);
        }

        // Include all language-specific overrides
        const languageSettings = this.configuration.get<Record<string, any>>('languages');
        if (languageSettings) {
            settings.languages = languageSettings;
        }

        return settings;
    }

    // Enhanced: Comprehensive configuration validation
    public validateConfiguration(): { valid: boolean; errors: string[] } {
        const errors: string[] = [];

        // Validate API URL
        const apiUrl = this.getApiUrl();
        if (!apiUrl || !this.isValidUrl(apiUrl)) {
            errors.push('Invalid API URL. Please provide a valid HTTP/HTTPS URL.');
        }

        // Validate general numeric ranges
        const maxSuggestions = this.configuration.get<number>('maxSuggestions', 3);
        if (maxSuggestions < 1 || maxSuggestions > 10) {
            errors.push('General max suggestions must be between 1 and 10.');
        }

        const temperature = this.configuration.get<number>('temperature', 0.7);
        if (temperature < 0.0 || temperature > 2.0) {
            errors.push('General temperature must be between 0.0 and 2.0.');
        }

        const maxContextLines = this.configuration.get<number>('maxContextLines', 50);
        if (maxContextLines < 10 || maxContextLines > 200) {
            errors.push('General max context lines must be between 10 and 200.');
        }

        const topP = this.configuration.get<number>('topP', 0.9);
        if (topP < 0.0 || topP > 1.0) {
            errors.push('General top_p must be between 0.0 and 1.0.');
        }

        const topK = this.configuration.get<number>('topK', 50);
        if (topK < 1 || topK > 100) {
            errors.push('General top_k must be between 1 and 100.');
        }

        const repetitionPenalty = this.configuration.get<number>('repetitionPenalty', 1.1);
        if (repetitionPenalty < 0.5 || repetitionPenalty > 2.0) {
            errors.push('General repetition penalty must be between 0.5 and 2.0.');
        }

        const contextWindow = this.configuration.get<number>('contextWindow', 1024);
        if (contextWindow < 256 || contextWindow > 4096) {
            errors.push('General context window must be between 256 and 4096.');
        }

        // Validate general model selection
        const model = this.configuration.get<string>('model', 'auto');
        const validModels = ['codegpt', 'codebert', 'auto'];
        if (!validModels.includes(model)) {
            errors.push(`Invalid general model selection. Must be one of: ${validModels.join(', ')}`);
        }

        // Validate language-specific settings
        const languageSettings = this.configuration.get<Record<string, any>>('languages');
        if (languageSettings) {
            for (const langKey of Object.keys(languageSettings)) {
                const langConfig = languageSettings[langKey];
                
                if (langConfig.maxSuggestions !== undefined && (langConfig.maxSuggestions < 1 || langConfig.maxSuggestions > 10)) {
                    errors.push(`Max suggestions for '${langKey}' must be between 1 and 10.`);
                }
                
                if (langConfig.temperature !== undefined && (langConfig.temperature < 0.0 || langConfig.temperature > 2.0)) {
                    errors.push(`Temperature for '${langKey}' must be between 0.0 and 2.0.`);
                }
                
                if (langConfig.maxContextLines !== undefined && (langConfig.maxContextLines < 10 || langConfig.maxContextLines > 200)) {
                    errors.push(`Max context lines for '${langKey}' must be between 10 and 200.`);
                }
                
                if (langConfig.topP !== undefined && (langConfig.topP < 0.0 || langConfig.topP > 1.0)) {
                    errors.push(`Top_p for '${langKey}' must be between 0.0 and 1.0.`);
                }
                
                if (langConfig.topK !== undefined && (langConfig.topK < 1 || langConfig.topK > 100)) {
                    errors.push(`Top_k for '${langKey}' must be between 1 and 100.`);
                }
                
                if (langConfig.repetitionPenalty !== undefined && (langConfig.repetitionPenalty < 0.5 || langConfig.repetitionPenalty > 2.0)) {
                    errors.push(`Repetition penalty for '${langKey}' must be between 0.5 and 2.0.`);
                }
                
                if (langConfig.contextWindow !== undefined && (langConfig.contextWindow < 256 || langConfig.contextWindow > 4096)) {
                    errors.push(`Context window for '${langKey}' must be between 256 and 4096.`);
                }
                
                if (langConfig.model !== undefined && !validModels.includes(langConfig.model)) {
                    errors.push(`Invalid model selection for '${langKey}'. Must be one of: ${validModels.join(', ')}`);
                }
                
                if (langConfig.indentStyle !== undefined && langConfig.indentStyle !== 'spaces' && langConfig.indentStyle !== 'tabs') {
                    errors.push(`Invalid indent style for '${langKey}'. Must be 'spaces' or 'tabs'.`);
                }
                
                if (langConfig.indentSize !== undefined && (langConfig.indentSize < 1 || langConfig.indentSize > 8)) {
                    errors.push(`Indent size for '${langKey}' must be between 1 and 8.`);
                }
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    // New: Update language-specific configuration
    public async updateLanguageConfig(language: string, config: Record<string, any>): Promise<void> {
        const currentLanguages = this.configuration.get<Record<string, any>>('languages', {});
        const updatedLanguages = {
            ...currentLanguages,
            [language]: {
                ...currentLanguages[language],
                ...config
            }
        };
        
        await this.configuration.update('languages', updatedLanguages, vscode.ConfigurationTarget.Global);
        this.reloadConfiguration();
    }

    // New: Remove language-specific configuration
    public async removeLanguageConfig(language: string): Promise<void> {
        const currentLanguages = this.configuration.get<Record<string, any>>('languages', {});
        const updatedLanguages = { ...currentLanguages };
        delete updatedLanguages[language];
        
        await this.configuration.update('languages', updatedLanguages, vscode.ConfigurationTarget.Global);
        this.reloadConfiguration();
    }

    private isValidUrl(url: string): boolean {
        try {
            const parsedUrl = new URL(url);
            return parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:';
        } catch {
            return false;
        }
    }

    public async resetToDefaults(): Promise<void> {
        const config = vscode.workspace.getConfiguration(ConfigurationManager.CONFIG_SECTION);

        // Reset all configuration values to defaults
        await config.update('enabled', undefined, vscode.ConfigurationTarget.Global);
        await config.update('apiUrl', undefined, vscode.ConfigurationTarget.Global);
        await config.update('maxSuggestions', undefined, vscode.ConfigurationTarget.Global);
        await config.update('temperature', undefined, vscode.ConfigurationTarget.Global);
        await config.update('maxContextLines', undefined, vscode.ConfigurationTarget.Global);
        await config.update('autoTrigger', undefined, vscode.ConfigurationTarget.Global);
        await config.update('model', undefined, vscode.ConfigurationTarget.Global);
        await config.update('topP', undefined, vscode.ConfigurationTarget.Global);
        await config.update('topK', undefined, vscode.ConfigurationTarget.Global);
        await config.update('repetitionPenalty', undefined, vscode.ConfigurationTarget.Global);
        await config.update('contextWindow', undefined, vscode.ConfigurationTarget.Global);
        await config.update('languages', undefined, vscode.ConfigurationTarget.Global);

        this.reloadConfiguration();
    }
}