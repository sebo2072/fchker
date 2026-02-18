import React, { useState } from 'react';
import { ValidationResult } from '../services/ApiService';
import './VerificationCard.css';

interface VerificationCardProps {
    result: ValidationResult;
}

function renderWithBold(text: string): React.ReactNode {
    if (!text) return null;
    // Split on **bold** markers
    const boldParts = text.split(/\*\*(.*?)\*\*/g);
    return boldParts.map((part, i) => {
        if (i % 2 === 1) return <strong key={`b${i}`}>{part}</strong>;
        // Also handle single *italic*
        const italicParts = part.split(/\*(.*?)\*/g);
        return italicParts.map((ip, j) =>
            j % 2 === 1 ? <em key={`i${i}-${j}`}>{ip}</em> : ip
        );
    });
}

const VerificationCard: React.FC<VerificationCardProps> = ({ result }) => {
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
                            <div className="section-label">EXECUTIVE SUMMARY</div>
                            <p className="section-text">{renderWithBold(result.evidence_summary)}</p>
                        </div>
                    )}

                    {result.key_findings && result.key_findings.length > 0 && (
                        <div className="card-section">
                            <div className="section-label">KEY FINDINGS</div>
                            <ul className="findings-list">
                                {result.key_findings.map((finding, index) => (
                                    <li key={index}>{renderWithBold(finding)}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {result.sources && result.sources.length > 0 && (
                        <div className="card-section">
                            <div className="section-label">SOURCES</div>
                            <div className="sources-list">
                                {result.sources.map((source, index) => (
                                    <a
                                        key={index}
                                        href={source.uri}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="source-item"
                                    >
                                        <div className="source-title">{source.title || 'Untitled Source'}</div>
                                        {/* URL removed as per FIX 2a */}
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
