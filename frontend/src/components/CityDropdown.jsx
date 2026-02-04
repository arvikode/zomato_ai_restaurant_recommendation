import React, { useEffect, useState } from 'react';
import { MapPin } from 'lucide-react';

const CityDropdown = ({ value, onChange }) => {
    const [cities, setCities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchCities = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const response = await fetch(`${apiUrl}/cities`);
                if (!response.ok) throw new Error('Failed to load cities');
                const data = await response.json();
                setCities(data);
            } catch (err) {
                console.error(err);
                setError('Could not load cities');
            } finally {
                setLoading(false);
            }
        };

        fetchCities();
    }, []);

    return (
        <div className="form-group">
            <label htmlFor="city-input">
                <MapPin size={16} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'text-bottom' }} />
                Select City
            </label>
            <input
                id="city-input"
                list="cities-list"
                type="text"
                className="select-input"
                placeholder={loading ? "Loading cities..." : "Type or select a city..."}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={loading || error}
            />
            <datalist id="cities-list">
                {cities.map((city) => (
                    <option key={city} value={city} />
                ))}
            </datalist>
            {error && <span style={{ color: 'var(--error)', fontSize: '0.8rem' }}>{error}</span>}
        </div>
    );
};

export default CityDropdown;
