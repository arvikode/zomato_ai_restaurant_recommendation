import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import RestaurantCard from './RestaurantCard';

describe('RestaurantCard', () => {
    const mockData = {
        rank: 1,
        name: 'Test Restaurant',
        location: 'Test Location',
        rating: 4.5,
        cost_for_two: 800,
        online_order: true,
        reason: 'Great food'
    };

    it('renders restaurant details correctly', () => {
        render(<RestaurantCard data={mockData} />);

        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('Test Restaurant')).toBeInTheDocument();
        expect(screen.getByText(/Test Location/i)).toBeInTheDocument();
        expect(screen.getByText('4.5')).toBeInTheDocument();
        expect(screen.getByText(/800/)).toBeInTheDocument();
        expect(screen.getByText('Online Delivery Available')).toBeInTheDocument();
        expect(screen.getByText('"Great food"')).toBeInTheDocument();
    });

    it('renders no delivery correctly', () => {
        const noDeliveryData = { ...mockData, online_order: false };
        render(<RestaurantCard data={noDeliveryData} />);
        expect(screen.getByText('No Online Delivery')).toBeInTheDocument();
    });
});
