import React from 'react';
import { DollarSign } from 'lucide-react';

const PriceDropdown = ({ value, onChange }) => {
    return (
        <div className="form-group">
            <label htmlFor="price-select">
                <DollarSign size={16} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
                Price Range
            </label>
            <select
                id="price-select"
                className="select-input"
                value={value}
                onChange={(e) => onChange(e.target.value)}
            >
                <option value="$">Budget ($)</option>
                <option value="$$">Standard ($$)</option>
                <option value="$$$">Premium ($$$)</option>
            </select>
        </div>
    );
};

export default PriceDropdown;
