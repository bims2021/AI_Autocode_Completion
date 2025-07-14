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

export class StatisticsManager {
    private stats!: CompletionStats;
    private responseTimes: number[] = [];
    private readonly maxResponseTimeHistory = 100;

    constructor(private context: vscode.ExtensionContext) {
        this.loadStatistics();
        this.setupAutoSave();
    }

    private loadStatistics(): void {
        const savedStats = this.context.globalState.get<CompletionStats>('completionStats');
        
        if (savedStats) {
            this.stats = {
                ...savedStats,
                sessionStartTime: Date.now() // Reset session start time
            };
        } else {
            this.stats = {
                totalRequests: 0,
                totalSuggestions: 0,
                acceptedSuggestions: 0,
                cacheHits: 0,
                averageResponseTime: 0,
                errorCount: 0,
                languageStats: {},
                dailyStats: {},
                sessionStartTime: Date.now()
            };
        }
    }

    private setupAutoSave(): void {
        // Save statistics every 5 minutes
        setInterval(() => {
            this.saveStatistics();
        }, 5 * 60 * 1000);
    }

    public recordCompletion(
        language: string,
        suggestionCount: number,
        responseTime: number,
        cacheHit: boolean
    ): void {
        // Update global stats
        this.stats.totalRequests++;
        this.stats.totalSuggestions += suggestionCount;
        
        if (cacheHit) {
            this.stats.cacheHits++;
        }

        // Update response time
        this.responseTimes.push(responseTime);
        if (this.responseTimes.length > this.maxResponseTimeHistory) {
            this.responseTimes.shift();
        }
        this.stats.averageResponseTime = this.responseTimes.reduce((a, b) => a + b, 0) / this.responseTimes.length;

        // Update language-specific stats
        if (!this.stats.languageStats[language]) {
            this.stats.languageStats[language] = {
                requests: 0,
                suggestions: 0,
                accepted: 0,
                avgResponseTime: 0
            };
        }
        
        const langStats = this.stats.languageStats[language];
        langStats.requests++;
        langStats.suggestions += suggestionCount;
        langStats.avgResponseTime = ((langStats.avgResponseTime * (langStats.requests - 1)) + responseTime) / langStats.requests;

        // Update daily stats
        const today = new Date().toISOString().split('T')[0];
        if (!this.stats.dailyStats[today]) {
            this.stats.dailyStats[today] = {
                requests: 0,
                accepted: 0
            };
        }
        this.stats.dailyStats[today].requests++;
    }

    public recordAcceptance(language: string): void {
        this.stats.acceptedSuggestions++;
        
        if (this.stats.languageStats[language]) {
            this.stats.languageStats[language].accepted++;
        }

        const today = new Date().toISOString().split('T')[0];
        if (this.stats.dailyStats[today]) {
            this.stats.dailyStats[today].accepted++;
        }
    }

    public recordCacheHit(): void {
        this.stats.cacheHits++;
    }

    public recordError(errorType: string): void {
        this.stats.errorCount++;
        // Could expand to track different error types
    }

    public getStatistics(): CompletionStats {
        return { ...this.stats };
    }

    public getAcceptanceRate(): number {
        if (this.stats.totalSuggestions === 0) {
            return 0;
        }
        return (this.stats.acceptedSuggestions / this.stats.totalSuggestions) * 100;
    }

    public getCacheHitRate(): number {
        if (this.stats.totalRequests === 0) {
            return 0;
        }
        return (this.stats.cacheHits / this.stats.totalRequests) * 100;
    }

    public getSessionDuration(): number {
        return Date.now() - this.stats.sessionStartTime;
    }

    public async showStatistics(): Promise<void> {
        const stats = this.getStatistics();
        const acceptanceRate = this.getAcceptanceRate();
        const cacheHitRate = this.getCacheHitRate();
        const sessionDuration = this.getSessionDuration();

        // Create statistics webview
        const panel = vscode.window.createWebviewPanel(
            'aiCompletionStats',
            'AI Completion Statistics',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        panel.webview.html = this.generateStatsHTML(stats, acceptanceRate, cacheHitRate, sessionDuration);
    }

    private generateStatsHTML(
        stats: CompletionStats,
        acceptanceRate: number,
        cacheHitRate: number,
        sessionDuration: number
    ): string {
        const sessionHours = Math.floor(sessionDuration / (1000 * 60 * 60));
        const sessionMinutes = Math.floor((sessionDuration % (1000 * 60 * 60)) / (1000 * 60));

        const languageStatsHTML = Object.entries(stats.languageStats)
            .map(([lang, langStats]) => {
                const langAcceptanceRate = langStats.suggestions > 0 
                    ? (langStats.accepted / langStats.suggestions * 100).toFixed(1)
                    : '0';
                
                return `
                    <tr>
                        <td>${lang}</td>
                        <td>${langStats.requests}</td>
                        <td>${langStats.suggestions}</td>
                        <td>${langStats.accepted}</td>
                        <td>${langAcceptanceRate}%</td>
                        <td>${Math.round(langStats.avgResponseTime)}ms</td>
                    </tr>
                `;
            })
            .join('');

        return `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>AI Completion Statistics</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        padding: 20px;
                        background-color: var(--vscode-editor-background);
                        color: var(--vscode-editor-foreground);
                    }
                    .stats-container {
                        max-width: 800px;
                        margin: 0 auto;
                    }
                    .stats-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin-bottom: 30px;
                    }
                    .stat-card {
                        background: var(--vscode-editor-inactiveSelectionBackground);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: 8px;
                        padding: 20px;
                        text-align: center;
                    }
                    .stat-value {
                        font-size: 2em;
                        font-weight: bold;
                        color: var(--vscode-textLink-foreground);
                        margin-bottom: 5px;
                    }
                    .stat-label {
                        font-size: 0.9em;
                        opacity: 0.8;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }
                    th, td {
                        text-align: left;
                        padding: 12px;
                        border-bottom: 1px solid var(--vscode-panel-border);
                    }
                    th {
                        background: var(--vscode-editor-inactiveSelectionBackground);
                        font-weight: 600;
                    }
                    .section-title {
                        font-size: 1.5em;
                        font-weight: bold;
                        margin: 30px 0 15px 0;
                        color: var(--vscode-textLink-foreground);
                    }
                </style>
            </head>
            <body>
                <div class="stats-container">
                    <h1>AI Code Completion Statistics</h1>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">${stats.totalRequests}</div>
                            <div class="stat-label">Total Requests</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.totalSuggestions}</div>
                            <div class="stat-label">Total Suggestions</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${acceptanceRate.toFixed(1)}%</div>
                            <div class="stat-label">Acceptance Rate</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${cacheHitRate.toFixed(1)}%</div>
                            <div class="stat-label">Cache Hit Rate</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${Math.round(stats.averageResponseTime)}ms</div>
                            <div class="stat-label">Avg Response Time</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${sessionHours}h ${sessionMinutes}m</div>
                            <div class="stat-label">Session Duration</div>
                        </div>
                    </div>

                    <div class="section-title">Language Statistics</div>
                    <table>
                        <thead>
                            <tr>
                                <th>Language</th>
                                <th>Requests</th>
                                <th>Suggestions</th>
                                <th>Accepted</th>
                                <th>Acceptance Rate</th>
                                <th>Avg Response Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${languageStatsHTML}
                        </tbody>
                    </table>
                </div>
            </body>
            </html>
        `;
    }

    public saveStatistics(): void {
        this.context.globalState.update('completionStats', this.stats);
    }

    public resetStatistics(): void {
        this.stats = {
            totalRequests: 0,
            totalSuggestions: 0,
            acceptedSuggestions: 0,
            cacheHits: 0,
            averageResponseTime: 0,
            errorCount: 0,
            languageStats: {},
            dailyStats: {},
            sessionStartTime: Date.now()
        };
        this.responseTimes = [];
        this.saveStatistics();
    }
}