import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }
    static getDerivedStateFromError(error) { return { hasError: true }; }
    componentDidCatch(error, errorInfo) { console.error(">>> Component Crash Handled:", error, errorInfo); }
    render() {
        if (this.state.hasError) {
            return (
                <div className="p-8 rounded-3xl border border-danger/20 bg-danger/5 text-center">
                    <p className="text-sm text-danger font-medium">Interactive component failed to load.</p>
                </div>
            );
        }
        return this.props.children;
    }
}

export default ErrorBoundary;
