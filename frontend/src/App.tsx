import React, { useEffect } from 'react';
import { useAppStore } from './store/appStore';
import { wsClient, WebSocketMessage } from './services/WebSocketClient';
import { apiService } from './services/ApiService';
import Header from './components/Header';
import InputPane from './components/InputPane';
import ThinkingPane from './components/ThinkingPane';
import ResultsPane from './components/ResultsPane';
import ClaimConfirmation from './components/ClaimConfirmation';
import { PaneTab } from './components/PaneTab';
import './App.css';

type FocusPane = 'input' | 'thinking' | 'results';

function App() {
    const {
        sessionId,
        setSessionId,
        status,
        setStatus,
        setStatusMessage,
        setError,
        addThinkingUpdate,
        addVerificationResult,
        setExtractedClaims,
        focusPane,
        setFocusPane,
        verificationResults
    } = useAppStore();

    // Initialization effect...

    // Initialize session on mount
    useEffect(() => {
        const initSession = async () => {
            if (sessionId) return; // Already initialized

            try {
                const { session_id } = await apiService.createSession();
                setSessionId(session_id);
                wsClient.connect(session_id);
                console.log('Session initialized:', session_id);
            } catch (error) {
                console.error('Failed to initialize session:', error);
                setError('Failed to connect to server');
            }
        };

        initSession();

        return () => {
            // Only disconnect on true unmount
            wsClient.disconnect();
        };
    }, []); // Empty dependency array for one-time initialization

    // Refs for synchronization
    const pendingClaimsRef = React.useRef<any[] | null>(null);
    const pendingResultsRef = React.useRef<{ [claimId: string]: any }>({});
    const { thinkingUpdates, setThinkingDisplayComplete } = useAppStore();

    // Handle WebSocket messages
    useEffect(() => {
        const handleMessage = (message: WebSocketMessage) => {
            switch (message.type) {
                case 'thinking_update':
                    addThinkingUpdate(message.data);
                    // Shift focus when thinking starts
                    if (focusPane !== 'results') {
                        setFocusPane('thinking');
                    }
                    break;

                case 'verification_result':
                    // Store in pending buffer
                    pendingResultsRef.current[message.data.claim_id] = message.data;
                    break;

                case 'claims_extracted':
                    pendingClaimsRef.current = message.data.claims;
                    setExtractedClaims(message.data.claims);
                    setStatusMessage('Finishing analysis...');
                    break;

                case 'status':
                    setStatusMessage(message.data.message || message.data.status);
                    if (message.data.status) {
                        setStatus(message.data.status);

                        // Auto-shifting focus based on backend status
                        if (message.data.status === 'extracting' || message.data.status === 'verifying') {
                            setFocusPane('thinking');
                        }
                    }
                    break;

                case 'error':
                    setError(message.data.error);
                    setStatus('error');
                    break;

                default:
                    console.warn('Unknown message type:', message.type);
            }
        };

        wsClient.addMessageHandler(handleMessage);

        return () => {
            wsClient.removeMessageHandler(handleMessage);
        };
    }, [
        addThinkingUpdate,
        setExtractedClaims,
        setStatus,
        setStatusMessage,
        setError,
        focusPane,
        setFocusPane
    ]);

    // Effect to monitor thinking display completion and trigger UI transitions
    useEffect(() => {
        // 1. Sync Extraction -> Confirmation
        if (status === 'extracting') {
            const extractionThinking = thinkingUpdates.find(u =>
                u.claim_id === 'extraction_thinking' && u.is_streaming_complete
            );

            if (extractionThinking?.isDisplayComplete && pendingClaimsRef.current) {
                setStatus('awaiting_confirmation');
                setStatusMessage('Review and confirm claims');
                pendingClaimsRef.current = null;
            }
        }

        // 2. Sync Verification Result -> Display
        if (status === 'verifying' || status === 'completed') {
            thinkingUpdates.forEach(update => {
                if (update.phase === 'completed' && update.isDisplayComplete) {
                    const pendingResult = pendingResultsRef.current[update.claim_id];
                    if (pendingResult) {
                        addVerificationResult(pendingResult);
                        delete pendingResultsRef.current[update.claim_id];

                        // Shift focus when first result appears
                        if (verificationResults.length === 0) {
                            setFocusPane('results');
                        }
                    }
                }
            });

            // Auto-complete if all verifications done and displayed
            const allThinkingFinished = thinkingUpdates.every(u =>
                u.phase !== 'completed' || u.isDisplayComplete
            );
            const noPendingResults = Object.keys(pendingResultsRef.current).length === 0;

            if (status === 'completed' && allThinkingFinished && noPendingResults && focusPane !== 'results') {
                setFocusPane('results');
            }
        }
    }, [thinkingUpdates, status, setStatus, setStatusMessage, addVerificationResult, verificationResults.length, setFocusPane]);

    // Manual focus override
    const handlePaneClick = (pane: FocusPane) => {
        // Prevent manual switching during confirmation dialog
        if (status === 'awaiting_confirmation') return;
        setFocusPane(pane);
    };

    const isBackground = (pane: FocusPane) => focusPane !== pane;

    return (
        <div className="app-shell">
            <Header />

            <main className="workspace">
                {/* 1. Persistent Tab Row - always visible atop the pane stack */}
                <div className="pane-tab-row">
                    <PaneTab
                        label="Input"
                        isActive={focusPane === 'input'}
                        onClick={() => handlePaneClick('input')}
                    />

                    {status !== 'idle' && (
                        <PaneTab
                            label="Thinking"
                            isActive={focusPane === 'thinking'}
                            onClick={() => handlePaneClick('thinking')}
                            isLive={status === 'extracting' || status === 'verifying'}
                        />
                    )}

                    {verificationResults.length > 0 && (
                        <PaneTab
                            label="Results"
                            isActive={focusPane === 'results'}
                            onClick={() => handlePaneClick('results')}
                            statusBadge={`${verificationResults.length} validated`}
                        />
                    )}
                </div>

                {/* 2. Pane Bodies - Stacked directly below tabs */}

                {/* Input Pane - Always rendered */}
                {focusPane === 'input' && (
                    <div className="pane-body">
                        <InputPane />
                    </div>
                )}

                {/* Thinking Pane - Rendered if active or background */}
                {/* Thinking Pane - Rendered if active or background */}
                {/* Fix: Always render if status is not idle, hide via CSS to preserve state */}
                {status !== 'idle' && (
                    <div
                        className={`pane-body ${focusPane !== 'thinking' ? 'pane-hidden' : ''}`}
                        onClick={() => focusPane !== 'thinking' && handlePaneClick('thinking')}
                    >
                        <ThinkingPane />
                    </div>
                )}

                {/* Re-evaluating: The brief implies a strict "Stack". 
                   Let's follow the standard "Active View" pattern first to ensure it works.
                   The Tabs provide the navigation.
                */}
                {focusPane === 'results' && (
                    <div className="pane-body">
                        <ResultsPane />
                    </div>
                )}

            </main>

            {/* 3. Confirmation Overlay - Portal/Absolute on top of everything */}
            {status === 'awaiting_confirmation' && (
                <div className="confirmation-overlay">
                    <div className="confirmation-backdrop" />
                    <ClaimConfirmation />
                </div>
            )}

            <footer className="app-footer">
                <span>FactChecker · Agentic Editorial System · v1.0</span>
            </footer>
        </div>
    );
}

export default App;
