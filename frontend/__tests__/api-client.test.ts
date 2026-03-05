/**
 * Tests for frontend/lib/api-client.ts
 *
 * Uses Jest's fetch mocking (via jest-environment-jsdom's globalThis.fetch).
 * No real HTTP calls are made.
 */

import ApiClient, {
  WaitlistError,
  UnauthorizedError,
  getAuthToken,
  apiClient,
} from '../lib/api-client';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build a Response-like mock that fetch will return.
 *  Uses a plain object instead of `new Response()` because jsdom may not
 *  expose the Fetch API Response global in all jest-environment-jsdom versions.
 */
function mockResponse(body: unknown, status = 200): object {
  const data = body;
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    blob: () => Promise.resolve(new Blob([JSON.stringify(data)])),
  };
}

function mockBlobResponse(status = 200): object {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.reject(new Error('not json')),
    blob: () => Promise.resolve(new Blob(['audio'], { type: 'audio/mpeg' })),
  };
}

// ---------------------------------------------------------------------------
// Setup: replace globalThis.fetch with a jest mock before each test
// ---------------------------------------------------------------------------

let fetchMock: jest.Mock;

beforeEach(() => {
  fetchMock = jest.fn();
  globalThis.fetch = fetchMock;
});

afterEach(() => {
  jest.resetAllMocks();
});

// ---------------------------------------------------------------------------
// getAuthToken
// ---------------------------------------------------------------------------

describe('getAuthToken', () => {
  it('returns the token string on success', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ token: 'my-token-abc' }));
    const token = await getAuthToken();
    expect(token).toBe('my-token-abc');
  });

  it('returns null when response is not ok', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, 401));
    const token = await getAuthToken();
    expect(token).toBeNull();
  });

  it('returns null when token field is missing', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ other: 'value' }));
    const token = await getAuthToken();
    expect(token).toBeNull();
  });

  it('returns null when fetch throws', async () => {
    fetchMock.mockRejectedValueOnce(new Error('Network error'));
    const token = await getAuthToken();
    expect(token).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// ApiClient instantiation and auth headers
// ---------------------------------------------------------------------------

describe('ApiClient auth headers', () => {
  it('does not include Authorization when no token getter is set', async () => {
    const client = new ApiClient('http://localhost:8080');
    fetchMock.mockResolvedValueOnce(mockResponse({ status: 'healthy', service: 'callpilot' }));
    await client.healthCheck();

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit?];
    expect((init?.headers as Record<string, string> | undefined)?.Authorization).toBeUndefined();
  });

  it('includes Authorization header when token getter returns a token', async () => {
    const client = new ApiClient('http://localhost:8080');
    client.setAuthTokenGetter(async () => 'test-jwt');
    fetchMock.mockResolvedValueOnce(mockResponse({ task_id: 'abc', status: 'gathering_info' }));
    await client.createTask();

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit?];
    const headers = init?.headers as Record<string, string>;
    expect(headers?.Authorization).toBe('Bearer test-jwt');
  });

  it('does not include Authorization when token getter returns null', async () => {
    const client = new ApiClient('http://localhost:8080');
    client.setAuthTokenGetter(async () => null);
    fetchMock.mockResolvedValueOnce(mockResponse({ task_id: 'abc', status: 'gathering_info' }));
    await client.createTask();

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit?];
    const headers = init?.headers as Record<string, string>;
    expect(headers?.Authorization).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// healthCheck
// ---------------------------------------------------------------------------

describe('ApiClient.healthCheck', () => {
  const client = new ApiClient('http://localhost:8080');

  it('calls GET /health', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ status: 'healthy', service: 'callpilot' }));
    await client.healthCheck();
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8080/health');
  });

  it('returns parsed body on success', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ status: 'healthy', service: 'callpilot' }));
    const result = await client.healthCheck();
    expect(result.status).toBe('healthy');
    expect(result.service).toBe('callpilot');
  });

  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, 503));
    await expect(client.healthCheck()).rejects.toThrow('Health check failed');
  });
});

// ---------------------------------------------------------------------------
// createBookingRequest
// ---------------------------------------------------------------------------

describe('ApiClient.createBookingRequest', () => {
  const client = new ApiClient('http://localhost:8080');

  it('calls POST /api/booking/request', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ booking_id: 'bid-1', status: 'processing', results: [] })
    );
    await client.createBookingRequest({
      service_type: 'dentist',
      timeframe: 'this week',
      location: 'Boston',
    });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('http://localhost:8080/api/booking/request');
    expect(init.method).toBe('POST');
  });

  it('includes request body', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ booking_id: 'bid-1', status: 'processing', results: [] })
    );
    await client.createBookingRequest({
      service_type: 'dentist',
      timeframe: 'this week',
      location: 'Boston',
    });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(init.body as string);
    expect(body.service_type).toBe('dentist');
    expect(body.location).toBe('Boston');
  });

  it('throws with error message from response on failure', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ error: 'Service unavailable' }, 503));
    await expect(
      client.createBookingRequest({ service_type: 'dentist', timeframe: 'today', location: 'NYC' })
    ).rejects.toThrow('Service unavailable');
  });
});

// ---------------------------------------------------------------------------
// getBookingStatus
// ---------------------------------------------------------------------------

describe('ApiClient.getBookingStatus', () => {
  const client = new ApiClient('http://localhost:8080');

  it('calls GET /api/booking/:id', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ booking_id: 'bid-1', status: 'completed', results: [] })
    );
    await client.getBookingStatus('bid-1');
    const [url] = fetchMock.mock.calls[0] as [string];
    expect(url).toBe('http://localhost:8080/api/booking/bid-1');
  });

  it('returns booking data', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ booking_id: 'bid-1', status: 'processing', results: [] })
    );
    const result = await client.getBookingStatus('bid-1');
    expect(result.booking_id).toBe('bid-1');
    expect(result.status).toBe('processing');
  });

  it('throws on 404', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ error: 'Booking not found' }, 404));
    await expect(client.getBookingStatus('nonexistent')).rejects.toThrow('Booking not found');
  });
});

// ---------------------------------------------------------------------------
// pollBookingStatus
// ---------------------------------------------------------------------------

describe('ApiClient.pollBookingStatus', () => {
  const client = new ApiClient('http://localhost:8080');

  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('resolves immediately when booking is already completed', async () => {
    fetchMock.mockResolvedValue(
      mockResponse({ booking_id: 'bid-1', status: 'completed', results: [] })
    );
    const result = await client.pollBookingStatus('bid-1', undefined, 10000);
    expect(result.status).toBe('completed');
  });

  it('resolves when status transitions to completed', async () => {
    // First call: processing; second call: completed
    fetchMock
      .mockResolvedValueOnce(
        mockResponse({ booking_id: 'bid-1', status: 'processing', results: [] })
      )
      .mockResolvedValueOnce(
        mockResponse({ booking_id: 'bid-1', status: 'completed', results: [{ provider_name: 'Clinic' }] })
      );

    const pollPromise = client.pollBookingStatus('bid-1', undefined, 30000);

    // advanceTimersByTimeAsync fires timers AND flushes the async promise chain
    await jest.advanceTimersByTimeAsync(2000);

    const result = await pollPromise;
    expect(result.status).toBe('completed');
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('calls onUpdate callback with each status', async () => {
    fetchMock.mockResolvedValue(
      mockResponse({ booking_id: 'bid-1', status: 'completed', results: [] })
    );
    const onUpdate = jest.fn();
    await client.pollBookingStatus('bid-1', onUpdate, 10000);
    expect(onUpdate).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'completed' })
    );
  });

  it('throws when timeout is exceeded', async () => {
    fetchMock.mockResolvedValue(
      mockResponse({ booking_id: 'bid-1', status: 'processing', results: [] })
    );

    const pollPromise = client.pollBookingStatus('bid-1', undefined, 1000);

    // Attach the rejection handler BEFORE advancing timers so the rejection
    // is never unhandled (which would cause the test to fail or warn).
    const assertion = expect(pollPromise).rejects.toThrow('timed out');

    // Advance past the 2-second sleep; Date.now() will exceed the 1-second timeout
    await jest.advanceTimersByTimeAsync(3000);

    await assertion;
  });
});

// ---------------------------------------------------------------------------
// getDashboardStats — WaitlistError and UnauthorizedError
// ---------------------------------------------------------------------------

describe('ApiClient.getDashboardStats error handling', () => {
  const client = new ApiClient('http://localhost:8080');

  it('throws WaitlistError on 403 with code=waitlist', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ error: 'Unauthorized', code: 'waitlist' }, 403)
    );
    await expect(client.getDashboardStats()).rejects.toThrow(WaitlistError);
  });

  it('WaitlistError has code property set to waitlist', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ error: 'Unauthorized', code: 'waitlist' }, 403)
    );
    try {
      await client.getDashboardStats();
    } catch (e) {
      expect(e).toBeInstanceOf(WaitlistError);
      expect((e as WaitlistError).code).toBe('waitlist');
    }
  });

  it('throws UnauthorizedError on 401', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ error: 'Unauthorized' }, 401));
    await expect(client.getDashboardStats()).rejects.toThrow(UnauthorizedError);
  });

  it('throws generic Error on other failures', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ error: 'Internal server error' }, 500)
    );
    const promise = client.getDashboardStats();
    await expect(promise).rejects.toThrow('Internal server error');
    await expect(promise).rejects.not.toThrow(WaitlistError);
  });

  it('returns data on success', async () => {
    const payload = {
      stats: { total_bookings: 5, completed: 3, processing: 2, total_calls_made: 10, success_rate: 0.6 },
      recent_bookings: [],
    };
    fetchMock.mockResolvedValueOnce(mockResponse(payload));
    const result = await client.getDashboardStats();
    expect(result.stats.total_bookings).toBe(5);
  });
});

// ---------------------------------------------------------------------------
// getDashboardBookings
// ---------------------------------------------------------------------------

describe('ApiClient.getDashboardBookings', () => {
  const client = new ApiClient('http://localhost:8080');

  it('throws WaitlistError on 403 waitlist', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ error: 'Unauthorized', code: 'waitlist' }, 403)
    );
    await expect(client.getDashboardBookings()).rejects.toThrow(WaitlistError);
  });

  it('throws UnauthorizedError on 401', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ error: 'Unauthorized' }, 401));
    await expect(client.getDashboardBookings()).rejects.toThrow(UnauthorizedError);
  });

  it('returns bookings array on success', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ bookings: [{ booking_id: '1' }] }));
    const result = await client.getDashboardBookings();
    expect(result.bookings).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// chat
// ---------------------------------------------------------------------------

describe('ApiClient.chat', () => {
  const client = new ApiClient('http://localhost:8080');

  it('calls POST /api/chat with correct body', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ reply: 'Got it!', extracted_data: {}, task_status: 'gathering_info', task_id: 'tid-1' })
    );
    await client.chat('tid-1', 'I need a dentist');
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('http://localhost:8080/api/chat');
    expect(init.method).toBe('POST');
    const body = JSON.parse(init.body as string);
    expect(body.task_id).toBe('tid-1');
    expect(body.message).toBe('I need a dentist');
  });

  it('returns parsed reply and task_status', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ reply: 'Got it!', extracted_data: { service_type: 'dentist' }, task_status: 'gathering_info', task_id: 'tid-1' })
    );
    const result = await client.chat('tid-1', 'hello');
    expect(result.reply).toBe('Got it!');
    expect(result.task_status).toBe('gathering_info');
  });

  it('throws on error response', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ error: 'Chat failed' }, 500));
    await expect(client.chat('tid-1', 'hello')).rejects.toThrow('Chat failed');
  });
});

// ---------------------------------------------------------------------------
// createTask
// ---------------------------------------------------------------------------

describe('ApiClient.createTask', () => {
  const client = new ApiClient('http://localhost:8080');

  it('calls POST /api/task', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ task_id: 'tid-1', status: 'gathering_info' }));
    await client.createTask();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('http://localhost:8080/api/task');
    expect(init.method).toBe('POST');
  });

  it('returns task_id', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ task_id: 'tid-abc', status: 'gathering_info' }));
    const result = await client.createTask();
    expect(result.task_id).toBe('tid-abc');
  });
});

// ---------------------------------------------------------------------------
// getConnections
// ---------------------------------------------------------------------------

describe('ApiClient.getConnections', () => {
  const client = new ApiClient('http://localhost:8080');

  it('throws WaitlistError on 403 waitlist', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ error: 'Unauthorized', code: 'waitlist' }, 403)
    );
    await expect(client.getConnections()).rejects.toThrow(WaitlistError);
  });

  it('throws UnauthorizedError on 401', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ error: 'Unauthorized' }, 401));
    await expect(client.getConnections()).rejects.toThrow(UnauthorizedError);
  });

  it('returns connections on success', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ connections: { google: true } }));
    const result = await client.getConnections();
    expect(result.connections).toEqual({ google: true });
  });
});

// ---------------------------------------------------------------------------
// Singleton export
// ---------------------------------------------------------------------------

describe('apiClient singleton', () => {
  it('is an instance of ApiClient', () => {
    expect(apiClient).toBeInstanceOf(ApiClient);
  });
});

// ---------------------------------------------------------------------------
// WaitlistError and UnauthorizedError classes
// ---------------------------------------------------------------------------

describe('WaitlistError', () => {
  it('has name WaitlistError', () => {
    const err = new WaitlistError();
    expect(err.name).toBe('WaitlistError');
  });

  it('has code waitlist', () => {
    const err = new WaitlistError();
    expect(err.code).toBe('waitlist');
  });

  it('is an instance of Error', () => {
    expect(new WaitlistError()).toBeInstanceOf(Error);
  });
});

describe('UnauthorizedError', () => {
  it('has name UnauthorizedError', () => {
    const err = new UnauthorizedError();
    expect(err.name).toBe('UnauthorizedError');
  });

  it('uses default message when none provided', () => {
    const err = new UnauthorizedError();
    expect(err.message).toBe('Unauthorized');
  });

  it('uses custom message when provided', () => {
    const err = new UnauthorizedError('Token expired');
    expect(err.message).toBe('Token expired');
  });

  it('is an instance of Error', () => {
    expect(new UnauthorizedError()).toBeInstanceOf(Error);
  });
});
