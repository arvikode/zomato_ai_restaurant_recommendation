import React from 'react';
import { Sparkles, Loader2 } from 'lucide-react';

const RecommendButton = ({ onClick, loading, disabled }) => {
    return (
        <button
            className="btn-primary"
            onClick={onClick}
            disabled={loading || disabled}
        >
            {loading ? (
                <>
                    <Loader2 className="animate-spin" size={20} />
                    Thinking...
                </>
            ) : (
                <>
                    <Sparkles size={20} />
                    Get Recommendations
                </>
            )}
        </button>
    );
};

export default RecommendButton;
