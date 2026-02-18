import React from 'react';
import './PaneTab.css';

interface PaneTabProps {
    label: string;
    isActive: boolean;
    onClick: () => void;
    statusBadge?: string;
    isLive?: boolean;
}

export const PaneTab: React.FC<PaneTabProps> = ({
    label,
    isActive,
    onClick,
    statusBadge,
    isLive
}) => {
    return (
        <div
            className={`pane-tab ${isActive ? 'active' : ''}`}
            onClick={onClick}
        >
            {isLive && <div className="pane-tab-dot" />}
            <span className="pane-tab-label">{label}</span>
            {statusBadge && <span className="pane-tab-badge">{statusBadge}</span>}
        </div>
    );
};
