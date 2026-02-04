import React from 'react';
import { Star, MapPin, IndianRupee, CheckCircle, XCircle } from 'lucide-react';

const RestaurantCard = ({ data, style }) => {
    const { rank, name, location, rating, cost_for_two, online_order, reason } = data;

    // Format rating color
    const getRatingColor = (r) => {
        if (r >= 4.5) return '#10b981'; // Green
        if (r >= 4.0) return '#84cc16'; // Light green
        if (r >= 3.5) return '#f59e0b'; // Amber
        return '#ef4444'; // Red
    };

    return (
        <div className="glass-panel animate-fade-in" style={{ padding: '1.5rem', position: 'relative', display: 'flex', flexDirection: 'column', gap: '0.75rem', ...style }}>
            <div style={{ position: 'absolute', top: -10, left: -10, width: 32, height: 32, background: 'var(--accent-gradient)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: 'white', fontSize: '1.2rem', boxShadow: '0 4px 6px rgba(0,0,0,0.3)' }}>
                {rank}
            </div>

            <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.25rem', color: 'var(--text-primary)' }}>{name}</h3>
                <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    <MapPin size={14} style={{ marginRight: 4 }} />
                    {location}
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', fontWeight: 600 }}>
                    <Star size={16} fill={getRatingColor(rating)} stroke="none" style={{ marginRight: 4 }} />
                    <span style={{ color: getRatingColor(rating) }}>{rating}</span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginLeft: 4 }}>/ 5</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-primary)' }}>
                    <IndianRupee size={14} />
                    {cost_for_two} <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginLeft: 4 }}>for two</span>
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: online_order ? 'var(--success)' : 'var(--text-secondary)' }}>
                {online_order ? <CheckCircle size={14} /> : <XCircle size={14} />}
                {online_order ? 'Online Delivery Available' : 'No Online Delivery'}
            </div>

            <div style={{ marginTop: '0.5rem', padding: '0.75rem', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '8px', borderLeft: '3px solid var(--accent-primary)' }}>
                <p style={{ fontSize: '0.9rem', fontStyle: 'italic', color: 'var(--text-primary)', lineHeight: '1.4' }}>
                    "{reason}"
                </p>
            </div>
        </div>
    );
};

export default RestaurantCard;
