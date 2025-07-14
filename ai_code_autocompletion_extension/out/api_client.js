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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.APIClient = void 0;
const axios_1 = __importDefault(require("axios"));
const os = __importStar(require("os"));
const crypto = __importStar(require("crypto"));
class APIClient {
    constructor(configManager) {
        this.configManager = configManager;
        this.requestTimeout = 10000; // 10 seconds
        this.userId = this.generateUserId();
        this.sessionId = this.generateSessionId();
        this.initializeHttpClient();
    }
    initializeHttpClient() {
        this.httpClient = axios_1.default.create({
            baseURL: this.configManager.getApiUrl(),
            timeout: this.requestTimeout,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'VSCode-AI-Completion/1.0.0'
            }
        });
        // Add request interceptor for logging
        this.httpClient.interceptors.request.use((config) => {
            console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
            return config;
        }, (error) => {
            console.error('API Request Error:', error);
            return Promise.reject(error);
        });
        // Add response interceptor for error handling
        this.httpClient.interceptors.response.use((response) => {
            console.log(`API Response: ${response.status} - ${response.config.url}`);
            return response;
        }, (error) => {
            console.error('API Response Error:', error.response?.status, error.message);
            return Promise.reject(error);
        });
    }
    async getSuggestions(context) {
        try {
            // Detect or get language from context
            const language = this.detectLanguage(context);
            const request = {
                context,
                language,
                max_suggestions: this.configManager.getMaxSuggestions(language),
                max_length: this.getMaxLength(language),
                temperature: this.configManager.getTemperature(language),
                user_id: this.userId,
                session_id: this.sessionId,
                preferences: {
                    model: this.configManager.getModel(language),
                    auto_trigger: this.configManager.getAutoTrigger(),
                    context_window: this.configManager.getMaxContextLines(language)
                }
            };
            const startTime = Date.now();
            const response = await this.httpClient.post('/api/v1/completions', request);
            const processingTime = Date.now() - startTime;
            // Validate response structure
            if (!this.isValidSuggestionResponse(response.data)) {
                throw new Error('Invalid response format from API');
            }
            // Add processing time to metadata
            response.data.metadata.processingTimeMs = processingTime;
            response.data.metadata.languageDetected = language; // Add language to metadata
            return response.data;
        }
        catch (error) {
            console.error('API call failed:', error);
            // Return error response
            return {
                suggestions: [],
                metadata: {
                    processingTimeMs: 0,
                    modelVersion: 'unknown',
                    cacheHit: false,
                    contextHash: '',
                    languageDetected: this.detectLanguage(context)
                },
                status: 'error',
                errorMessage: this.getErrorMessage(error)
            };
        }
    }
    async sendFeedback(suggestionIndex, accepted, context) {
        try {
            const language = this.detectLanguage(context);
            await this.httpClient.post('/api/v1/feedback', {
                user_id: this.userId,
                session_id: this.sessionId,
                suggestion_index: suggestionIndex,
                accepted,
                context_hash: this.generateContextHash(context),
                language,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            console.error('Failed to send feedback:', error);
            // Don't throw error for feedback failures
        }
    }
    async checkHealth() {
        try {
            const response = await this.httpClient.get('/health', { timeout: 5000 });
            return response.status === 200;
        }
        catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }
    async getModelInfo() {
        try {
            const response = await this.httpClient.get('/api/v1/models');
            return response.data;
        }
        catch (error) {
            console.error('Failed to get model info:', error);
            return null;
        }
    }
    // New: Get language-specific model configurations
    async getLanguageConfig(language) {
        try {
            const response = await this.httpClient.get(`/api/v1/config/language/${language}`);
            return response.data;
        }
        catch (error) {
            console.error(`Failed to get config for language ${language}:`, error);
            return null;
        }
    }
    updateConfiguration(configManager) {
        this.configManager = configManager;
        this.httpClient.defaults.baseURL = configManager.getApiUrl();
    }
    clearCache() {
        // Send cache clear request to backend
        this.httpClient.post('/api/v1/cache/clear', {
            user_id: this.userId,
            session_id: this.sessionId
        }).catch(error => {
            console.error('Failed to clear backend cache:', error);
        });
    }
    // New: Clear language-specific cache
    clearLanguageCache(language) {
        this.httpClient.post('/api/v1/cache/clear', {
            user_id: this.userId,
            session_id: this.sessionId,
            language
        }).catch(error => {
            console.error(`Failed to clear cache for language ${language}:`, error);
        });
    }
    detectLanguage(context) {
        // Primary: Use context.language if available
        if (context.language) {
            return context.language.toLowerCase();
        }
        // Secondary: Try to detect from file extension
        if (context.filePath) {
            const ext = context.filePath.split('.').pop()?.toLowerCase();
            const langMap = {
                'py': 'python',
                'js': 'javascript',
                'ts': 'typescript',
                'jsx': 'javascript',
                'tsx': 'typescript',
                'java': 'java',
                'cpp': 'cpp',
                'cc': 'cpp',
                'cxx': 'cpp',
                'c': 'c',
                'cs': 'c#',
                'go': 'go',
                'rs': 'rust',
                'php': 'php',
                'rb': 'ruby',
                'swift': 'swift',
                'kt': 'kotlin',
                'scala': 'scala',
                'html': 'html',
                'css': 'css',
                'sql': 'sql',
                'sh': 'bash',
                'ps1': 'powershell'
            };
            if (ext && langMap[ext]) {
                return langMap[ext];
            }
        }
        // Fallback: Return 'unknown' or 'text'
        return 'unknown';
    }
    getMaxLength(language) {
        // Get language-specific max length from configuration
        // This could be extended to be more sophisticated
        const contextLines = this.configManager.getMaxContextLines(language);
        // Rough estimate: average 50 characters per line
        return Math.min(contextLines * 50, 2048);
    }
    isValidSuggestionResponse(data) {
        return (data &&
            Array.isArray(data.suggestions) &&
            data.metadata &&
            typeof data.metadata.processingTimeMs === 'number' &&
            typeof data.metadata.modelVersion === 'string' &&
            typeof data.metadata.cacheHit === 'boolean' &&
            typeof data.status === 'string');
    }
    getErrorMessage(error) {
        if (error.response) {
            // Server responded with error status
            return `Server error: ${error.response.status} - ${error.response.data?.message || error.response.statusText}`;
        }
        else if (error.request) {
            // Request was made but no response received
            return 'No response from server. Please check your connection and API URL.';
        }
        else if (error.code === 'ECONNABORTED') {
            // Request timeout
            return 'Request timeout. The AI service is taking too long to respond.';
        }
        else {
            // Something else happened
            return `Request failed: ${error.message}`;
        }
    }
    generateUserId() {
        // Generate a consistent user ID based on machine/workspace
        const machineId = os.hostname();
        return crypto.createHash('sha256').update(machineId).digest('hex').substring(0, 16);
    }
    generateSessionId() {
        // Generate a new session ID for each VS Code session
        return crypto.randomUUID();
    }
    generateContextHash(context) {
        const contextString = JSON.stringify({
            currentLine: context.currentLine,
            language: context.language,
            functionContext: context.functionContext,
            filePath: context.filePath
        });
        return crypto.createHash('md5').update(contextString).digest('hex');
    }
}
exports.APIClient = APIClient;
//# sourceMappingURL=api_client.js.map