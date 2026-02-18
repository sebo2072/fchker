import React, { useState, useRef } from 'react';
import { useAppStore } from '../store/appStore';
import { apiService } from '../services/ApiService';
import './InputPane.css';

const InputPane: React.FC = () => {
    const {
        mode,
        setMode,
        sessionId,
        inputText,
        setInputText,
        extractedClaims,
        setExtractedClaims,
        addVerificationResult,
        setStatus,
        setStatusMessage,
        setError,
        error,
        reset,
        setFocusPane,
    } = useAppStore();

    const [isProcessing, setIsProcessing] = useState(false);
    const [showHighlights, setShowHighlights] = useState(true);
    const [isDragging, setIsDragging] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize effect for programmatic changes
    React.useEffect(() => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = 'auto';
        el.style.height = `${el.scrollHeight}px`;
    }, [inputText]);

    const handleSubmit = async () => {
        if (!inputText.trim() || !sessionId) return;
        if (mode === 'single' && inputText.length > 100) {
            setError('Single fact must be under 100 characters');
            return;
        }

        setIsProcessing(true);
        setError(null);
        reset();

        try {
            if (mode === 'single') {
                setStatus('verifying');
                setStatusMessage('Validating fact...');
                setFocusPane('thinking');
                const result = await apiService.verifySingleClaim(inputText, sessionId);
                if (result && result.result) {
                    addVerificationResult(result.result);
                }
            } else {
                setStatus('extracting');
                setStatusMessage('Extracting and validating facts...');
                setFocusPane('thinking');
                const result = await apiService.analyzeText(inputText, sessionId);
                if (result && result.claims) {
                    setExtractedClaims(result.claims);
                    setStatus('awaiting_confirmation');
                    setStatusMessage('Review and confirm claims');
                }
            }
        } catch (error: any) {
            setError(error.message || 'An error occurred');
            setStatus('error');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleFileUpload = async (file: File) => {
        if (!file || !sessionId) return;
        if (file.size > 5 * 1024 * 1024) {
            setError('File size exceeds 5MB limit');
            return;
        }

        setIsProcessing(true);
        setError(null);

        try {
            // Check file type
            const extension = file.name.split('.').pop()?.toLowerCase();
            let result;
            if (extension === 'pdf') {
                result = await apiService.uploadPDF(file, sessionId);
                setInputText(result.extracted_text);
                setStatusMessage(`Extracted ${result.text_length} characters from PDF`);
            } else if (extension === 'txt' || extension === 'docx') {
                // Placeholder for extended support - using existing PDF endpoint logic 
                // but frontend sends to backend for processing.
                // Note: Actual extended backend support will be implemented in a later step.
                result = await apiService.uploadPDF(file, sessionId);
                setInputText(result.extracted_text);
                setStatusMessage(`Extracted from ${extension.toUpperCase()}`);
            } else {
                setError('Unsupported file type');
            }
        } catch (error: any) {
            setError(error.message || 'Failed to process file');
        } finally {
            setIsProcessing(false);
        }
    };

    const onDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const onDragLeave = () => {
        setIsDragging(false);
    };

    const onDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (mode === 'bulk' && e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    };

    const renderTextWithHighlights = () => {
        if (!inputText || !extractedClaims.length || !showHighlights) {
            return inputText;
        }

        const claimsWithVerbatim = extractedClaims
            .filter(c => c.verbatim && c.verbatim.trim())
            .sort((a, b) => b.verbatim.length - a.verbatim.length);

        if (!claimsWithVerbatim.length) return inputText;

        let segments: (string | JSX.Element)[] = [inputText];

        claimsWithVerbatim.forEach((claim) => {
            const newSegments: (string | JSX.Element)[] = [];
            segments.forEach((seg) => {
                if (typeof seg !== 'string') {
                    newSegments.push(seg);
                    return;
                }

                let verbatimToUse = claim.verbatim;
                let parts = seg.split(verbatimToUse);

                if (parts.length === 1) {
                    try {
                        const escapedVerbatim = verbatimToUse.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        const fuzzyPattern = escapedVerbatim.replace(/\s+/g, '\\s+');
                        const match = seg.match(new RegExp(fuzzyPattern, 'i'));

                        if (match) {
                            verbatimToUse = match[0];
                            parts = seg.split(verbatimToUse);
                        }
                    } catch (e) { }
                }

                if (parts.length > 1) {
                    parts.forEach((part, i) => {
                        newSegments.push(part);
                        if (i < parts.length - 1) {
                            newSegments.push(
                                <span key={`${claim.id}-${i}`} className="verbatim-highlight" title={claim.claim}>
                                    {verbatimToUse}
                                </span>
                            );
                        }
                    });
                } else {
                    newSegments.push(seg);
                }
            });
            segments = newSegments;
        });

        return segments;
    };

    return (
        <div className={`input-pane ${mode === 'single' ? 'mode-single' : 'mode-bulk'}`}>
            <div className="mode-toggle-container">
                <div className="mode-toggle">
                    <button
                        className={`toggle-btn ${mode === 'bulk' ? 'active' : ''}`}
                        onClick={() => setMode('bulk')}
                    >
                        LARGE TEXT
                    </button>
                    <button
                        className={`toggle-btn ${mode === 'single' ? 'active' : ''}`}
                        onClick={() => setMode('single')}
                    >
                        SINGLE FACT
                    </button>
                </div>
            </div>

            <div
                className={`input-section ${isDragging ? 'dragging' : ''}`}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
            >
                {extractedClaims.length > 0 && mode === 'bulk' && showHighlights ? (
                    <div className="input-viewer">
                        {renderTextWithHighlights()}
                    </div>
                ) : (
                    <textarea
                        ref={textareaRef}
                        className="input-textarea"
                        placeholder={
                            mode === 'single'
                                ? 'Enter a single factual claim (max 100 chars)...'
                                : 'Paste article or drop files here (.pdf, .txt, .docx, max 5MB)...'
                        }
                        value={inputText}
                        maxLength={mode === 'single' ? 100 : undefined}
                        onChange={(e) => {
                            setInputText(e.target.value);
                            e.target.style.height = 'auto';
                            e.target.style.height = `${e.target.scrollHeight}px`;
                        }}
                        disabled={isProcessing}
                    />
                )}

                <div className="input-actions">
                    {mode === 'bulk' && (
                        <div className="file-actions">
                            <button
                                className="upload-btn"
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isProcessing}
                            >
                                Upload File
                            </button>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".pdf,.txt,.docx"
                                onChange={(e) => e.target.files && handleFileUpload(e.target.files[0])}
                                disabled={isProcessing}
                                style={{ display: 'none' }}
                            />
                        </div>
                    )}

                    <div className="submit-group">
                        {error && <div className="inline-error">{error}</div>}
                        <button
                            className="primary-submit-btn"
                            onClick={handleSubmit}
                            disabled={!inputText.trim() || isProcessing}
                        >
                            {isProcessing ? (
                                'Processing...'
                            ) : mode === 'single' ? (
                                'Validate Fact'
                            ) : (
                                'Extract Facts & Validate'
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {mode === 'bulk' && extractedClaims.length > 0 && (
                <button
                    className="toggle-highlights-btn"
                    onClick={() => setShowHighlights(!showHighlights)}
                >
                    {showHighlights ? 'HIDE HIGHLIGHTS' : 'SHOW HIGHLIGHTS'}
                </button>
            )}
        </div>
    );
};

export default InputPane;
