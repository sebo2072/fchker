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

    // Handle WebSocket messages
    useEffect(() => {
        const handleMessage = (message: WebSocketMessage) => {
            switch (message.type) {
                case 'thinking_update':
                    addThinkingUpdate(message.data);
                    // Shift focus when thinking starts (Fix: use direct value, not function updater)
                    if (focusPane !== 'results') {
                        setFocusPane('thinking');
                    }
                    break;

                case 'verification_result':
                    addVerificationResult(message.data);
                    // Shift focus when results start appearing
                    setFocusPane('results');
                    break;

                case 'claims_extracted':
                    setExtractedClaims(message.data.claims);
                    setStatus('awaiting_confirmation');
                    setStatusMessage('Review and confirm claims');
                    break;

                case 'status':
                    setStatusMessage(message.data.message || message.data.status);
                    if (message.data.status) {
                        setStatus(message.data.status);

                        // Auto-shifting focus based on backend status
                        if (message.data.status === 'extracting' || message.data.status === 'verifying') {
                            setFocusPane('thinking');
                        } else if (message.data.status === 'completed') {
                            setFocusPane('results');
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
        addVerificationResult,
        setExtractedClaims,
        setStatus,
        setStatusMessage,
        setError,
    ]);

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
