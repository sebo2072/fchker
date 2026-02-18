import React from 'react';
import { useAppStore } from '../store/appStore';
import VerificationCard from './VerificationCard';
import './ResultsPane.css';

const ResultsPane: React.FC = () => {
    const { verificationResults } = useAppStore();

    return (
        <div className="results-pane">
            {verificationResults.length > 0 && (
                <div className="results-count-header">
                    <span>VERIFICATION FINDINGS</span>
                    <span>{verificationResults.length} validated</span>
                </div>
            )}

            {verificationResults.length === 0 ? (
                <div className="empty-state">
                    <p>No results yet.</p>
                </div>
            ) : (
                <div className="results-list">
                    {verificationResults.map((result, index) => (
                        <VerificationCard key={result.claim_id || index} result={result} />
                    ))}
                </div>
            )}
        </div>
    );
};

export default ResultsPane;
