/**
 * API Client for CallPilot Backend
 * Handles all communication with the Flask API.
 * When getToken is set, all requests include Authorization: Bearer <token> for auth.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

/** Thrown when backend returns 403 with code 'waitlist' (user not yet in allowed pool). */
export class WaitlistError extends Error {
  code = 'waitlist';
  constructor() {
    super("You're on the waitlist. We'll add you soon.");
    this.name = 'WaitlistError';
  }
}

/** Thrown when backend returns 401 (token missing/invalid or backend NEXTAUTH_SECRET not set). */
export class UnauthorizedError extends Error {
  constructor(message = 'Unauthorized') {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

/** Fetches the current session JWT from the frontend auth API. Use this when calling from the client. */
export async function getAuthToken(): Promise<string | null> {
  try {
    const res = await fetch('/api/auth/token', { credentials: 'include' });
    if (!res.ok) return null;
    const data = await res.json();
    return data.token ?? null;
  } catch {
    return null;
  }
}

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
    /** User-stated time (e.g. "6 PM") so calendar slots match */
    preferred_time?: string;
    /** For restaurant: party size (e.g. "6") */
    party_size?: string;
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

export type GetAuthToken = () => Promise<string | null>;

class ApiClient {
  private baseUrl: string;
  private getToken: GetAuthToken | null = null;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  /** Set a function that returns the current auth token. Required for protected backend routes. */
  setAuthTokenGetter(getToken: GetAuthToken) {
    this.getToken = getToken;
  }

  private async authHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.getToken) {
      const token = await this.getToken();
      if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  /**
   * Health check endpoint (no auth required)
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
      headers: await this.authHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error((error as { error?: string }).error || 'Failed to create booking request');
    }

    return response.json();
  }

  /**
   * Get booking status by ID
   */
  async getBookingStatus(bookingId: string): Promise<BookingStatus> {
    const response = await fetch(`${this.baseUrl}/api/booking/${bookingId}`, {
      headers: await this.authHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error((error as { error?: string }).error || 'Failed to get booking status');
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
      headers: await this.authHeaders(),
      body: JSON.stringify({ provider_id: providerId }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
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

  /** Dashboard stats (protected) */
  async getDashboardStats(): Promise<{
    stats: {
      total_bookings: number;
      completed: number;
      processing: number;
      total_calls_made: number;
      success_rate: number;
    };
    recent_bookings: Array<Record<string, unknown>>;
  }> {
    const response = await fetch(`${this.baseUrl}/api/dashboard/stats`, {
      headers: await this.authHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({})) as { error?: string; code?: string };
      if (response.status === 403 && err.code === 'waitlist') throw new WaitlistError();
      if (response.status === 401) throw new UnauthorizedError(err.error || 'Unauthorized');
      throw new Error(err.error || 'Failed to fetch dashboard stats');
    }
    return response.json();
  }

  /** All bookings for dashboard (protected) */
  async getDashboardBookings(): Promise<{ bookings: Array<Record<string, unknown>> }> {
    const response = await fetch(`${this.baseUrl}/api/dashboard/bookings`, {
      headers: await this.authHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({})) as { error?: string; code?: string };
      if (response.status === 403 && err.code === 'waitlist') throw new WaitlistError();
      if (response.status === 401) throw new UnauthorizedError(err.error || 'Unauthorized');
      throw new Error(err.error || 'Failed to fetch bookings');
    }
    return response.json();
  }

  /** Create a new task (protected) */
  async createTask(): Promise<{ task_id: string; status: string }> {
    const response = await fetch(`${this.baseUrl}/api/task`, {
      method: 'POST',
      headers: await this.authHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error((err as { error?: string }).error || 'Failed to create task');
    }
    return response.json();
  }

  /** Send chat message (protected) */
  async chat(taskId: string, message: string): Promise<{
    reply: string;
    extracted_data: Record<string, unknown>;
    task_status: string;
    task_id: string;
  }> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: await this.authHeaders(),
      body: JSON.stringify({ task_id: taskId, message }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error((err as { error?: string }).error || 'Chat failed');
    }
    return response.json();
  }

  /** Get task by id (protected) */
  async getTask(taskId: string): Promise<Record<string, unknown>> {
    const response = await fetch(`${this.baseUrl}/api/task/${taskId}`, {
      headers: await this.authHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error((err as { error?: string }).error || 'Task not found');
    }
    return response.json();
  }

  /** Connections status (protected) */
  async getConnections(): Promise<{ connections: Record<string, unknown> }> {
    const response = await fetch(`${this.baseUrl}/api/connections`, {
      headers: await this.authHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({})) as { error?: string; code?: string };
      if (response.status === 403 && err.code === 'waitlist') throw new WaitlistError();
      if (response.status === 401) throw new UnauthorizedError(err.error || 'Unauthorized');
      throw new Error(err.error || 'Failed to fetch connections');
    }
    return response.json();
  }

  /** Text-to-speech (protected). Returns audio blob. */
  async tts(text: string, voiceId?: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/tts`, {
      method: 'POST',
      headers: await this.authHeaders(),
      body: JSON.stringify({ text, voice_id: voiceId || 'EXAVITQu4vr4xnSDxMaL' }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error((err as { error?: string }).error || 'TTS failed');
    }
    return response.blob();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export default ApiClient;
