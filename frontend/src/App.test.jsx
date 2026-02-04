import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import App from './App';

describe('App Integration', () => {
    const mockCities = ['Bangalore'];
    const mockRecommendations = {
        recommendations: [
            {
                rank: 1,
                name: 'Test Cafe',
                location: 'Indiranagar',
                rating: 4.8,
                cost_for_two: 1200,
                online_order: true,
                reason: 'Excellent ambiance'
            }
        ]
    };

    beforeEach(() => {
        global.fetch = vi.fn((url) => {
            if (url.includes('/cities')) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve(mockCities),
                });
            }
            if (url.includes('/recommendations')) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve(mockRecommendations),
                });
            }
            return Promise.reject(new Error('Unknown URL'));
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders initial state correctly', async () => {
        render(<App />);
        expect(screen.getByText('AI Restaurant Guide')).toBeInTheDocument();
        expect(screen.getByText('Select a city to get started')).toBeInTheDocument();

        // Button should be disabled initially (no city selected)
        const button = screen.getByRole('button', { name: /get recommendations/i });
        expect(button).toBeDisabled();
    });

    it('allows full flow: select city -> get recommendations', async () => {
        render(<App />);

        // 1. Wait for cities to load
        await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/cities')));

        // 2. Select City
        const cityInput = screen.getByPlaceholderText('Type or select a city...');
        fireEvent.change(cityInput, { target: { value: 'Bangalore' } });

        // 3. Button should now be enabled
        const button = screen.getByRole('button', { name: /get recommendations/i });
        expect(button).not.toBeDisabled();

        // 4. Click button
        fireEvent.click(button);

        // 5. Check loading state (optional, might be too fast)
        // expect(screen.getByText(/Thinking.../i)).toBeInTheDocument();

        // 6. Wait for results
        await waitFor(() => {
            expect(screen.getByText('Test Cafe')).toBeInTheDocument();
            expect(screen.getByText('"Excellent ambiance"')).toBeInTheDocument();
        });
    });
});
