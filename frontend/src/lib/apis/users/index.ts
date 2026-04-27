import { WEBUI_API_BASE_URL } from '$lib/constants';

// Basic error handling function following Open WebUI pattern
const handleApiError = (err: any) => {
	console.error(err);
	return err.detail || err.message || err;
};

// ONLY the user functions that actually exist in your backend
export const getUserProfile = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/profile/`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
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

export const updateUserProfile = async (token: string, profile: object) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/profile/`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(profile)
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