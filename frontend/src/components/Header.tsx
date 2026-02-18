import React from 'react';
import { useAppStore } from '../store/appStore';
import './Header.css';

const Header: React.FC = () => {
    const { status, statusMessage, error } = useAppStore();

    return (
        <header className="header">
            <div className="header-content">
                <div className="header-left">
                    <a href="/" className="logo-link" aria-label="FactChecker Home">
                        <div className="logo-placeholder">
                            <div className="logo-img-area">
                                <span className="logo-text">FC</span>
                            </div>
                        </div>
                        <div className="logo-wordmark">
                            <span className="logo-name">FactChecker</span>
                            <span className="logo-sub">Agentic Editorial System</span>
                        </div>
                    </a>
                </div>

                <div className="header-right">
                    {error ? (
                        <div className="status-indicator error">
                            <span className="status-dot"></span>
                            ERROR DETECTED
                        </div>
                    ) : (
                        <div className={`status-indicator ${status}`}>
                            <span className="status-dot"></span>
                            {(statusMessage || status).replace('_', ' ')}
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
};

export default Header;
