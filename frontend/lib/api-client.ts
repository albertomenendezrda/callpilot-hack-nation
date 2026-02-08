/**
 * API Client for CallPilot Backend
 * Handles all communication with the Flask API
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export interface BookingRequest {
  service_type: string;
  timeframe: string;
  location: string;
  preferences?: {
    rating_weight?: number;
    distance_weight?: number;
    availability_weight?: number;
    /** Concrete availability windows (e.g. from calendar) so the agent can close in one call */
    preferred_slots?: string;
  };
}

export interface BookingResult {
  provider_name: string;
  provider_id: string;
  phone: string;
  address: string;
  rating: number;
  distance: number;
  travel_time: number;
  availability_date: string;
  availability_time: string;
  score: number;
}

export interface BookingStatus {
  booking_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  results: BookingResult[];
  message?: string;
}

export interface BookingConfirmation {
  status: 'confirmed' | 'failed';
  booking_id: string;
  message: string;
  calendar_event_id?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  }

  /**
   * Create a new booking request
   */
  async createBookingRequest(request: BookingRequest): Promise<BookingStatus> {
    const response = await fetch(`${this.baseUrl}/api/booking/request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create booking request');
    }

    return response.json();
  }

  /**
   * Get booking status by ID
   */
  async getBookingStatus(bookingId: string): Promise<BookingStatus> {
    const response = await fetch(`${this.baseUrl}/api/booking/${bookingId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get booking status');
    }

    return response.json();
  }

  /**
   * Confirm a booking with a specific provider
   */
  async confirmBooking(
    bookingId: string,
    providerId: string
  ): Promise<BookingConfirmation> {
    const response = await fetch(`${this.baseUrl}/api/booking/${bookingId}/confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ provider_id: providerId }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to confirm booking');
    }

    return response.json();
  }

  /**
   * Poll booking status until completed or timeout
   */
  async pollBookingStatus(
    bookingId: string,
    onUpdate?: (status: BookingStatus) => void,
    timeoutMs: number = 120000
  ): Promise<BookingStatus> {
    const startTime = Date.now();
    const pollInterval = 2000; // Poll every 2 seconds

    while (Date.now() - startTime < timeoutMs) {
      const status = await this.getBookingStatus(bookingId);

      if (onUpdate) {
        onUpdate(status);
      }

      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }

      // Wait before next poll
      await new Promise((resolve) => setTimeout(resolve, pollInterval));
    }

    throw new Error('Booking request timed out');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export default ApiClient;
