/**
 * API service for HTTP requests to the backend.
 */

const API_BASE_URL = '/api';

export interface Claim {
    id: string;
    claim: string;
    verbatim: string;
    context: string;
    type: string;
    is_quote: boolean;
    confidence: number;
}

export interface VerificationResult {
    claim_id: string;
    claim_text: string;
    claim_type: string;
    thinking_process: string;
    status: 'VERIFIED' | 'PARTIALLY_VERIFIED' | 'UNVERIFIED' | 'DISPUTED' | 'FALSE';
    confidence: number;
    evidence_summary: string;
    key_findings: string[];
    sources: any[];
}

class ApiService {
    async createSession(): Promise<{ session_id: string }> {
        const response = await fetch(`${API_BASE_URL}/create-session`, {
            method: 'POST',
        });

        if (!response.ok) {
            throw new Error('Failed to create session');
        }

        return response.json();
    }

    async verifySingleClaim(claim: string, sessionId?: string): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/verify-single`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                claim,
                session_id: sessionId,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to verify claim');
        }

        return response.json();
    }

    async analyzeText(text: string, sessionId?: string): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/analyze-text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text,
                session_id: sessionId,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to analyze text');
        }

        return response.json();
    }

    async confirmClaims(sessionId: string, confirmedClaims: Claim[]): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/confirm-claims`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                confirmed_claims: confirmedClaims,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to confirm claims');
        }

        return response.json();
    }

    async uploadPDF(file: File, sessionId?: string): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);
        if (sessionId) {
            formData.append('session_id', sessionId);
        }

        const response = await fetch(`${API_BASE_URL}/upload-pdf`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Failed to upload PDF');
        }

        return response.json();
    }

    async getSession(sessionId: string): Promise<any> {
        const response = await fetch(`${API_BASE_URL}/session/${sessionId}`);

        if (!response.ok) {
            throw new Error('Failed to get session');
        }

        return response.json();
    }
}

export const apiService = new ApiService();
