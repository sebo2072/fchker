import React, { useState } from 'react';
import { useAppStore } from '../store/appStore';
import VerificationCard from './VerificationCard';
import './ResultsPane.css';

const ResultsPane: React.FC = () => {
    const { verificationResults, status, reset, setFocusPane } = useAppStore();
    const [copied, setCopied] = useState(false);

    const handleNewTask = () => {
        reset();
        setFocusPane('input');
    };

    const handleCopyAll = () => {
        const text = verificationResults.map(result => {
            const statusText = result.status.replace(/_/g, ' ');
            const confidence = Math.round(result.confidence * 100);
            let block = `CLAIM: ${result.claim_text}\nSTATUS: ${statusText} (${confidence}% reliability)`;

            if (result.evidence_summary) {
                block += `\n\nEXECUTIVE SUMMARY:\n${result.evidence_summary}`;
            }
            if (result.key_findings?.length) {
                block += `\n\nKEY FINDINGS:\n${result.key_findings.map(f => `• ${f}`).join('\n')}`;
            }
            if (result.sources?.length) {
                block += `\n\nSOURCES:\n${result.sources.map(s =>
                    `${s.title || 'Untitled'}: ${s.uri || ''}`
                ).join('\n')}`;
            }
            return block;
        }).join('\n\n' + '─'.repeat(40) + '\n\n');

        navigator.clipboard.writeText(text).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    return (
        <div className="results-pane">
            {verificationResults.length > 0 && (
                <div className="results-count-header">
                    <span>Verification findings</span>
                    <div className="results-header-actions">
                        <span>{verificationResults.length} validated</span>
                        <button className="copy-btn" onClick={handleCopyAll}>
                            {copied ? '✓ Copied' : 'Copy all'}
                        </button>
                    </div>
                </div>
            )}

            {verificationResults.length === 0 ? (
                <div className="empty-state">
                    <p>No results yet.</p>
                </div>
            ) : (
                <>
                    <div className="results-list">
                        {verificationResults.map((result, index) => (
                            <VerificationCard key={result.claim_id || index} result={result} />
                        ))}
                    </div>

                    {status === 'completed' && (
                        <div className="new-task-container">
                            <button className="new-task-btn" onClick={handleNewTask}>
                                Start a new task
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default ResultsPane;
