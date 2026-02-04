import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import CityDropdown from './CityDropdown';

describe('CityDropdown', () => {
    const mockCities = ['Bangalore', 'Mumbai', 'Delhi'];

    beforeEach(() => {
        global.fetch = vi.fn(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockCities),
            })
        );
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('fetches and renders cities', async () => {
        const onChange = vi.fn();
        render(<CityDropdown value="" onChange={onChange} />);

        // Initial loading state might be fast, but we can check if fetch was called
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/cities'));

        // Wait for data to load
        await waitFor(() => {
            const input = screen.getByPlaceholderText('Type or select a city...');
            expect(input).toBeInTheDocument();
        });

        // Check if datalist options are present
        await waitFor(() => {
            const datalist = document.getElementById('cities-list');
            expect(datalist).toBeInTheDocument();
            expect(datalist.children.length).toBe(3);
        });
    });

    it('calls onChange when input changes', async () => {
        const onChange = vi.fn();
        render(<CityDropdown value="" onChange={onChange} />);

        await waitFor(() => screen.getByPlaceholderText('Type or select a city...'));

        const input = screen.getByPlaceholderText('Type or select a city...');
        fireEvent.change(input, { target: { value: 'Bangalore' } });

        expect(onChange).toHaveBeenCalledWith('Bangalore');
    });
});
