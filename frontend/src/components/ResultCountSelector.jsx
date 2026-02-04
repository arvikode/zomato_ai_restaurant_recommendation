import React from 'react';
import { List } from 'lucide-react';

const ResultCountSelector = ({ value, onChange }) => {
    return (
        <div className="form-group">
            <label htmlFor="count-select">
                <List size={16} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
                Number of Recommendations
            </label>
            <select
                id="count-select"
                className="select-input"
                value={value}
                onChange={(e) => onChange(Number(e.target.value))}
            >
                {[3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                    <option key={num} value={num}>{num} Recommendations</option>
                ))}
            </select>
        </div>
    );
};

export default ResultCountSelector;
