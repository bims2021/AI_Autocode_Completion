import * as vscode from 'vscode';
export interface CompletionStats {
    totalRequests: number;
    totalSuggestions: number;
    acceptedSuggestions: number;
    cacheHits: number;
    averageResponseTime: number;
    errorCount: number;
    languageStats: Record<string, {
        requests: number;
        suggestions: number;
        accepted: number;
        avgResponseTime: number;
    }>;
    dailyStats: Record<string, {
        requests: number;
        accepted: number;
    }>;
    sessionStartTime: number;
}
export declare class StatisticsManager {
    private context;
    private stats;
    private responseTimes;
    private readonly maxResponseTimeHistory;
    constructor(context: vscode.ExtensionContext);
    private loadStatistics;
    private setupAutoSave;
    recordCompletion(language: string, suggestionCount: number, responseTime: number, cacheHit: boolean): void;
    recordAcceptance(language: string): void;
    recordCacheHit(): void;
    recordError(errorType: string): void;
    getStatistics(): CompletionStats;
    getAcceptanceRate(): number;
    getCacheHitRate(): number;
    getSessionDuration(): number;
    showStatistics(): Promise<void>;
    private generateStatsHTML;
    saveStatistics(): void;
    resetStatistics(): void;
}
//# sourceMappingURL=statistics_manager.d.ts.map