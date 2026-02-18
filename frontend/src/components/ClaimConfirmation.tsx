import React from 'react';
import { useAppStore } from '../store/appStore';
import { apiService } from '../services/ApiService';
import './ClaimConfirmation.css';

const ClaimConfirmation: React.FC = () => {
    const {
        sessionId,
        extractedClaims,
        selectedClaims,
        toggleClaimSelection,
        selectAllClaims,
        deselectAllClaims,
        setStatus,
        setStatusMessage,
        setError,
    } = useAppStore();

    const handleConfirm = async () => {
        if (!sessionId || selectedClaims.length === 0) return;

        const confirmedClaimObjects = extractedClaims.filter(claim =>
            selectedClaims.includes(claim.id)
        );

        try {
            setStatus('verifying');
            setStatusMessage(`Validating ${confirmedClaimObjects.length} facts...`);
            await apiService.confirmClaims(sessionId, confirmedClaimObjects);
        } catch (error: any) {
            setError(error.message || 'Failed to verify claims');
            setStatus('error');
        }
    };

    const allSelected = selectedClaims.length === extractedClaims.length;

    return (
        <div className="claim-confirmation">
            <div className="confirmation-header">
                <h2 className="confirmation-title">Review Factual Claims</h2>
                <p className="confirmation-subtitle">
                    Found {extractedClaims.length} verifiable statements.
                    Select facts to proceed with deep validation.
                </p>
            </div>

            <div className="confirmation-body">
                <div className="claims-list">
                    {extractedClaims.map((claim) => (
                        <div
                            key={claim.id}
                            className={`claim-item ${selectedClaims.includes(claim.id) ? 'selected' : ''}`}
                            onClick={() => toggleClaimSelection(claim.id)}
                        >
                            <div className="claim-checkbox-wrapper">
                                <input
                                    type="checkbox"
                                    className="claim-checkbox"
                                    checked={selectedClaims.includes(claim.id)}
                                    readOnly
                                />
                            </div>
                            <div className="claim-content">
                                <div className="claim-text">{claim.claim}</div>
                                {claim.verbatim && (
                                    <div className="claim-verbatim">
                                        <span className="verbatim-label">VERBATIM:</span> "{claim.verbatim}"
                                    </div>
                                )}
                                <div className="claim-meta">
                                    <span className="claim-type">{claim.type}</span>
                                    <span className="claim-confidence">
                                        {Math.round(claim.confidence * 100)}% DETECTED CONFIDENCE
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="confirmation-footer">
                <button
                    className="action-link"
                    onClick={allSelected ? deselectAllClaims : selectAllClaims}
                >
                    {allSelected ? 'Deselect All' : 'Select All'}
                </button>
                <button
                    className="primary-confirm-btn"
                    onClick={handleConfirm}
                    disabled={selectedClaims.length === 0}
                >
                    Verify {selectedClaims.length} Selected
                </button>
            </div>
        </div>
    );
};

export default ClaimConfirmation;
