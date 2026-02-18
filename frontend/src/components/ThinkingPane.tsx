import React, { useEffect, useRef } from 'react';
import { useAppStore, ThinkingUpdate } from '../store/appStore';
import { useTypewriter } from '../hooks/useTypewriter';
import StatusLabel from './StatusLabel';
import './ThinkingPane.css';

interface ThinkingBlockProps {
    update: ThinkingUpdate;
    isLast: boolean;
}

const ThinkingBlock: React.FC<ThinkingBlockProps> = ({ update, isLast }) => {
    const { displayedText, isComplete } = useTypewriter(update.message, isLast ? 20 : 0);

    return (
        <div className={`thinking-block ${isLast ? 'active' : ''}`}>
            <div className="timeline-node">
                <div className="node-dot"></div>
                {!isLast && <div className="node-line"></div>}
            </div>
            <div className="block-content">
                {/* Block header removed as per addendum to fix "Invalid Date" and unwanted phases */}
                <div className="block-message">
                    {displayedText}
                    {!isComplete && isLast && <span className="blinking-cursor">_</span>}
                </div>
            </div>
        </div>
    );
};

const ThinkingPane: React.FC = () => {
    const { thinkingUpdates, status } = useAppStore();
    const scrollRef = useRef<HTMLDivElement>(null);

    // Filter out native_thought chunks as per addendum
    const displayUpdates = thinkingUpdates.filter(u => !u.is_native_thought);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [displayUpdates.length, status]);

    return (
        <div className="thinking-pane">
            <div className="thinking-scroll-area" ref={scrollRef}>
                <div className="thinking-timeline">
                    {displayUpdates.length === 0 && status === 'idle' ? (
                        <div className="empty-state">
                            <p>Agent is ready.</p>
                        </div>
                    ) : (
                        <>
                            {displayUpdates.map((update, index) => (
                                <ThinkingBlock
                                    // Stable key based on content identity
                                    key={`${update.claim_id}-${update.phase}-${update.is_delta ? 'delta' : 'static'}-${index}`}
                                    update={update}
                                    isLast={index === displayUpdates.length - 1 && status !== 'idle'}
                                />
                            ))}

                            {/* Rotating Status Label at the bottom */}
                            {(status === 'extracting' || status === 'verifying') && (
                                <StatusLabel />
                            )}

                            {status === 'completed' && (
                                <div className="completion-message" style={{
                                    marginTop: '24px',
                                    paddingLeft: '16px',
                                    color: 'var(--color-success)',
                                    fontWeight: 700,
                                    fontSize: '0.85rem'
                                }}>
                                    All tasks complete.
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ThinkingPane;
