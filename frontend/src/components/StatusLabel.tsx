import React, { useState, useEffect } from 'react';

const LABELS = [
    "Analyzing context...",
    "Extracting key claims...",
    "Cross-referencing sources...",
    "Evaluating evidence...",
    "Drafting verification...",
    "Refining response..."
];

const StatusLabel: React.FC = () => {
    const [index, setIndex] = useState(0);
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        const interval = setInterval(() => {
            setVisible(false);
            setTimeout(() => {
                setIndex((prev) => (prev + 1) % LABELS.length);
                setVisible(true);
            }, 300); // Wait for fade out
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div
            className="status-label-animated"
            style={{
                opacity: visible ? 1 : 0,
                transition: 'opacity 0.3s ease-in-out',
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'var(--color-primary)',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                marginTop: '16px',
                paddingLeft: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            }}
        >
            <div className="pulse-dot" style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--color-primary)',
                animation: 'pulse 1.5s infinite'
            }}></div>
            {LABELS[index]}
        </div>
    );
};

export default StatusLabel;
