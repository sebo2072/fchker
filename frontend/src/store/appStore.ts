/**
 * Global state management using Zustand.
 */
import { create } from 'zustand';
import { Claim, VerificationResult } from '../services/ApiService';

export interface ThinkingUpdate {
    claim_id: string;
    phase: string;
    message: string;
    is_native_thought?: boolean;
    is_refined?: boolean;
    is_delta?: boolean;
    is_streaming_complete?: boolean;
    result?: VerificationResult;
}

interface AppState {
    // Session
    sessionId: string | null;
    setSessionId: (id: string | null) => void;

    // Layout
    focusPane: 'input' | 'thinking' | 'results';
    setFocusPane: (pane: 'input' | 'thinking' | 'results') => void;
    // Mode
    mode: 'single' | 'bulk';
    setMode: (mode: 'single' | 'bulk') => void;

    // Input
    inputText: string;
    setInputText: (text: string) => void;

    // Claims
    extractedClaims: Claim[];
    setExtractedClaims: (claims: Claim[]) => void;
    selectedClaims: string[]; // IDs of selected claims
    toggleClaimSelection: (id: string) => void;
    selectAllClaims: () => void;
    deselectAllClaims: () => void;

    // Thinking updates
    thinkingUpdates: ThinkingUpdate[];
    addThinkingUpdate: (update: ThinkingUpdate) => void;
    clearThinkingUpdates: () => void;

    // Results
    verificationResults: VerificationResult[];
    addVerificationResult: (result: VerificationResult) => void;
    clearVerificationResults: () => void;

    // Status
    status: 'idle' | 'extracting' | 'awaiting_confirmation' | 'verifying' | 'completed' | 'error';
    setStatus: (status: AppState['status']) => void;
    statusMessage: string;
    setStatusMessage: (message: string) => void;

    // Error
    error: string | null;
    setError: (error: string | null) => void;

    // Reset
    reset: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
    // Session
    sessionId: null,
    setSessionId: (id) => set({ sessionId: id }),

    // Layout
    focusPane: 'input',
    setFocusPane: (pane) => set({ focusPane: pane }),
    // Mode
    mode: 'single',
    setMode: (mode) => set({ mode }),

    // Input
    inputText: '',
    setInputText: (text) => set({ inputText: text }),

    // Claims
    extractedClaims: [],
    setExtractedClaims: (claims) => set({ extractedClaims: claims }),
    selectedClaims: [],
    toggleClaimSelection: (id) => {
        const { selectedClaims } = get();
        if (selectedClaims.includes(id)) {
            set({ selectedClaims: selectedClaims.filter(cid => cid !== id) });
        } else {
            set({ selectedClaims: [...selectedClaims, id] });
        }
    },
    selectAllClaims: () => {
        const { extractedClaims } = get();
        set({ selectedClaims: extractedClaims.map(c => c.id) });
    },
    deselectAllClaims: () => set({ selectedClaims: [] }),

    // Thinking updates
    thinkingUpdates: [],
    addThinkingUpdate: (update) => {
        const { thinkingUpdates } = get();

        // 1. Handle Native Thought Chunks (append to last if same phase)
        if (update.is_native_thought) {
            const lastUpdate = thinkingUpdates[thinkingUpdates.length - 1];
            if (lastUpdate &&
                lastUpdate.claim_id === update.claim_id &&
                lastUpdate.phase === update.phase &&
                lastUpdate.is_native_thought) {

                const newUpdates = [...thinkingUpdates];
                newUpdates[newUpdates.length - 1] = {
                    ...lastUpdate,
                    message: lastUpdate.message + update.message
                };
                set({ thinkingUpdates: newUpdates });
                return;
            }
        }

        // 2. Handle Refined Narrative Streaming (REPLACE if same phase)
        if (update.is_delta || update.is_streaming_complete) {
            const existingIndex = thinkingUpdates.findIndex(u =>
                u.claim_id === update.claim_id &&
                u.phase === update.phase &&
                (u.is_delta || u.is_refined)
            );

            if (existingIndex !== -1) {
                const newUpdates = [...thinkingUpdates];
                newUpdates[existingIndex] = update;
                set({ thinkingUpdates: newUpdates });
                return;
            }
        }

        // 3. Otherwise append as new entry
        set({ thinkingUpdates: [...thinkingUpdates, update] });
    },
    clearThinkingUpdates: () => set({ thinkingUpdates: [] }),

    // Results
    verificationResults: [],
    addVerificationResult: (result) => {
        const { verificationResults } = get();
        set({ verificationResults: [...verificationResults, result] });
    },
    clearVerificationResults: () => set({ verificationResults: [] }),

    // Status
    status: 'idle',
    setStatus: (status) => set({ status }),
    statusMessage: '',
    setStatusMessage: (message) => set({ statusMessage: message }),

    // Error
    error: null,
    setError: (error) => set({ error }),

    // Reset
    reset: () => set({
        extractedClaims: [],
        selectedClaims: [],
        thinkingUpdates: [],
        verificationResults: [],
        status: 'idle',
        statusMessage: '',
        error: null,
    }),
}));
