import React, { useState } from 'react';
import { VerificationResult } from '../services/ApiService';
import './VerificationCard.css';

interface Props {
    result: VerificationResult;
}

const VerificationCard: React.FC<Props> = ({ result }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'VERIFIED':
                return 'verified';
            case 'PARTIALLY_VERIFIED':
                return 'partially-verified';
            case 'UNVERIFIED':
                return 'unverified';
            case 'DISPUTED':
            case 'FALSE':
                return 'false';
            default:
                return 'unverified';
        }
    };

    const getStatusText = (status: string) => status.replace('_', ' ');

    return (
        <div className={`verification-card ${getStatusColor(result.status)} ${isExpanded ? 'expanded' : ''}`}>
            <div className="card-header" onClick={() => setIsExpanded(!isExpanded)}>
                <div className="card-indicator"></div>
                <div className="card-title-section">
                    <div className="card-claim">{result.claim_text}</div>
                    <div className="card-meta">
                        <span className="status-label">{getStatusText(result.status)}</span>
                        <span className="confidence-label">
                            {Math.round(result.confidence * 100)}% RELIABILITY
                        </span>
                    </div>
                </div>
                <button className="expand-toggle">
                    {isExpanded ? 'COLLAPSE' : 'DETAILS'}
                </button>
            </div>

            {isExpanded && (
                <div className="card-body">
                    {result.evidence_summary && (
                        <div className="card-section">
                            <h4 className="section-label">Executive summary</h4>
                            <p className="section-text">{result.evidence_summary}</p>
                        </div>
                    )}

                    {result.key_findings && result.key_findings.length > 0 && (
                        <div className="card-section">
                            <h4 className="section-label">Critical findings</h4>
                            <ul className="findings-list">
                                {result.key_findings.map((finding, index) => (
                                    <li key={index}>{finding}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {result.sources && result.sources.length > 0 && (
                        <div className="card-section">
                            <h4 className="section-label">Validated sources</h4>
                            <div className="sources-grid">
                                {result.sources.map((source, index) => (
                                    <a
                                        key={index}
                                        href={source.uri || '#'}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="source-card"
                                    >
                                        <div className="source-title">{source.title || 'Untitled Source'}</div>
                                        <div className="source-url">{(source.uri || '').substring(0, 40)}...</div>
                                    </a>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default VerificationCard;
