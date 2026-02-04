import React, { useState } from 'react';
import { Utensils } from 'lucide-react';
import CityDropdown from './components/CityDropdown';
import PriceDropdown from './components/PriceDropdown';
import ResultCountSelector from './components/ResultCountSelector';
import RecommendButton from './components/RecommendButton';
import RestaurantCard from './components/RestaurantCard';

function App() {
  const [city, setCity] = useState('');
  const [price, setPrice] = useState('$$');
  const [limit, setLimit] = useState(5);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRecommend = async () => {
    if (!city) {
      setError('Please select a city first.');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/recommendations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          city,
          price_category: price,
          limit
        }),
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('No appropriate restaurants found for these criteria. Try adjusting your filters.');
        }
        if (response.status === 503) {
          throw new Error('Service busy or LLM error. Please try again.');
        }
        throw new Error('Failed to fetch recommendations.');
      }

      const data = await response.json();
      setResults(data.recommendations);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header style={{ marginBottom: '3rem', textAlign: 'center' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 64, height: 64, borderRadius: '50%', background: 'var(--accent-gradient)', marginBottom: '1.5rem', boxShadow: '0 10px 25px rgba(99, 102, 241, 0.5)' }}>
          <Utensils color="white" size={32} />
        </div>
        <h1 className="heading-gradient" style={{ display: 'block', fontSize: '3rem', marginBottom: '0.5rem', lineHeight: 1.2 }}>
          AI Restaurant Guide
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.2rem', maxWidth: '600px', margin: '0 auto' }}>
          Discover the perfect dining spot with AI-powered recommendations tailored to your taste and budget.
        </p>
      </header>

      <div className="glass-panel" style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
          <CityDropdown value={city} onChange={setCity} />
          <PriceDropdown value={price} onChange={setPrice} />
          <ResultCountSelector value={limit} onChange={setLimit} />
        </div>

        <RecommendButton onClick={handleRecommend} loading={loading} disabled={!city} />

        {error && (
          <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', borderRadius: '8px', color: 'var(--error)', textAlign: 'center' }}>
            {error}
          </div>
        )}
      </div>

      {results && (
        <div className="card-grid">
          {results.map((item, index) => (
            <RestaurantCard
              key={index}
              data={item}
              style={{ animationDelay: `${index * 100}ms` }}
            />
          ))}
        </div>
      )}

      {!results && !loading && !error && (
        <div style={{ textAlign: 'center', marginTop: '4rem', opacity: 0.5 }}>
          <p>Select a city to get started</p>
        </div>
      )}
    </div>
  );
}

export default App;
