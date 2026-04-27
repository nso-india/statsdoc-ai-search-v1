import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants/app';

// Enhanced error handling function following Open WebUI pattern
const handleApiError = (err: any) => {
	console.error('API Error:', err);
	
	// Return structured error object with more details
	if (err && typeof err === 'object') {
		// Handle different error response structures
		if (err.detail) {
			return err; // Return full error object to preserve structure
		}
		if (err.message) {
			return { detail: err.message, ...err };
		}
		if (err.error) {
			return { detail: err.error, ...err };
		}
		// Handle validation errors
		if (err.username || err.password || err.non_field_errors) {
			return err;
		}
	}
	
	// Fallback for string errors or unknown structures
	return { detail: err?.message || err || 'An unexpected error occurred' };
};

// ONLY the auth functions that actually exist in your backend
export const userSignIn = async (username: string, password: string) => {
	let error = null;

	try {
		// Create an AbortController for timeout handling
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

		const res = await fetch(`${WEBUI_API_BASE_URL}/login/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				email: username, // Send as 'email' field
				password: password
			}),
			signal: controller.signal
		});

		clearTimeout(timeoutId);

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({
				detail: `HTTP ${res.status}: ${res.statusText}`
			}));
			
			// Handle account lockout errors
			if (errorData.detail && typeof errorData.detail === 'string') {
				if (errorData.detail.includes('locked') || errorData.detail.includes('attempts')) {
					// Return full error object with lockout info
					throw errorData;
				}
			}
			
			throw errorData;
		}

		return await res.json();
	} catch (err: any) {
		// Handle network errors
		if (err.name === 'TypeError' && err.message.includes('fetch')) {
			throw handleApiError({
				detail: 'Unable to connect to server. Please check your internet connection.',
				type: 'network_error'
			});
		}
		
		// Handle timeout errors
		if (err.name === 'AbortError') {
			throw handleApiError({
				detail: 'Request timed out. Please try again.',
				type: 'timeout_error'
			});
		}

		// Handle API errors
		error = handleApiError(err);
		throw error;
	}
};

export const refreshToken = async (refresh: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/token/refresh/`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			refresh: refresh
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = handleApiError(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const verifyToken = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/token/verify/`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			token: token
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = handleApiError(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Get session user info - following Open WebUI pattern
export const getSessionUser = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/profile/`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = handleApiError(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Get current user role from the new user management API
export const getCurrentUserRole = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/users/me/role/`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = handleApiError(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// User sign out - following Open WebUI pattern
export const userSignOut = async () => {
	// For JWT tokens, we don't need to call the backend to sign out
	// We just remove the tokens from local storage (handled in the stores)
	return true;
};

// User signup with email verification
export const userSignUp = async (signupData: {
	first_name: string;
	last_name: string;
	email: string;
	phone: string;
	user_type: string;
	organization_name: string;
	password: string;
}) => {
	let error = null;

	try {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

		const res = await fetch(`${WEBUI_BASE_URL}/api/signup/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(signupData),
			signal: controller.signal
		});

		clearTimeout(timeoutId);

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({
				detail: `HTTP ${res.status}: ${res.statusText}`
			}));
			throw errorData;
		}

		return await res.json();
	} catch (err: any) {
		// Handle network errors
		if (err.name === 'TypeError' && err.message.includes('fetch')) {
			throw handleApiError({
				detail: 'Unable to connect to server. Please check your internet connection.',
				type: 'network_error'
			});
		}
		
		// Handle timeout errors
		if (err.name === 'AbortError') {
			throw handleApiError({
				detail: 'Request timed out. Please try again.',
				type: 'timeout_error'
			});
		}

		// Handle API errors
		error = handleApiError(err);
		throw error;
	}
};

// Email verification
export const verifyEmail = async (email: string, token: string) => {
	let error = null;

	try {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 30000);

		const res = await fetch(`${WEBUI_BASE_URL}/api/verify-email/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email, token }),
			signal: controller.signal
		});

		clearTimeout(timeoutId);

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({
				detail: `HTTP ${res.status}: ${res.statusText}`
			}));
			throw errorData;
		}

		return await res.json();
	} catch (err: any) {
		if (err.name === 'TypeError' && err.message.includes('fetch')) {
			throw handleApiError({
				detail: 'Unable to connect to server. Please check your internet connection.',
				type: 'network_error'
			});
		}
		
		if (err.name === 'AbortError') {
			throw handleApiError({
				detail: 'Request timed out. Please try again.',
				type: 'timeout_error'
			});
		}

		error = handleApiError(err);
		throw error;
	}
};

// Resend email verification
export const resendEmailVerification = async (email: string) => {
	let error = null;

	try {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 30000);

		const res = await fetch(`${WEBUI_BASE_URL}/api/resend-verification/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email }),
			signal: controller.signal
		});

		clearTimeout(timeoutId);

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({
				detail: `HTTP ${res.status}: ${res.statusText}`
			}));
			throw errorData;
		}

		return await res.json();
	} catch (err: any) {
		if (err.name === 'TypeError' && err.message.includes('fetch')) {
			throw handleApiError({
				detail: 'Unable to connect to server. Please check your internet connection.',
				type: 'network_error'
			});
		}
		
		if (err.name === 'AbortError') {
			throw handleApiError({
				detail: 'Request timed out. Please try again.',
				type: 'timeout_error'
			});
		}

		error = handleApiError(err);
		throw error;
	}
};

// Forgot password
export const forgotPassword = async (email: string) => {
	let error = null;

	try {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 30000);

		const res = await fetch(`${WEBUI_BASE_URL}/api/forgot-password/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email }),
			signal: controller.signal
		});

		clearTimeout(timeoutId);

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({
				detail: `HTTP ${res.status}: ${res.statusText}`
			}));
			throw errorData;
		}

		return await res.json();
	} catch (err: any) {
		if (err.name === 'TypeError' && err.message.includes('fetch')) {
			throw handleApiError({
				detail: 'Unable to connect to server. Please check your internet connection.',
				type: 'network_error'
			});
		}
		
		if (err.name === 'AbortError') {
			throw handleApiError({
				detail: 'Request timed out. Please try again.',
				type: 'timeout_error'
			});
		}

		error = handleApiError(err);
		throw error;
	}
};

// Reset password
export const resetPassword = async (email: string, token: string, newPassword: string) => {
	let error = null;

	try {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 30000);

		const res = await fetch(`${WEBUI_BASE_URL}/api/reset-password/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ 
				email,
				token,
				new_password: newPassword
			}),
			signal: controller.signal
		});

		clearTimeout(timeoutId);

		if (!res.ok) {
			const errorData = await res.json().catch(() => ({
				detail: `HTTP ${res.status}: ${res.statusText}`
			}));
			throw errorData;
		}

		return await res.json();
	} catch (err: any) {
		if (err.name === 'TypeError' && err.message.includes('fetch')) {
			throw handleApiError({
				detail: 'Unable to connect to server. Please check your internet connection.',
				type: 'network_error'
			});
		}
		
		if (err.name === 'AbortError') {
			throw handleApiError({
				detail: 'Request timed out. Please try again.',
				type: 'timeout_error'
			});
		}

		error = handleApiError(err);
		throw error;
	}
};