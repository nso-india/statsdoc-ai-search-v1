// Speech-to-Text API using OpenAI Whisper

import { tokenManager } from '$lib/auth/tokenManager';

// Proxy to server-side transcription endpoint to avoid CORS and keep OpenAI API key secure
async function transcribeWithWhisper(audioBlob: Blob): Promise<string> {
	try {

		const formData = new FormData();
		formData.append('file', audioBlob, 'audio.webm');
		formData.append('language', 'en');

		// Attach JWT if available via tokenManager
		const token = tokenManager.getToken();
		const headers: Record<string, string> = {};
		if (token) headers['Authorization'] = `Bearer ${token}`;

		const response = await fetch('/api/speech/transcribe/', {
			method: 'POST',
			headers: headers,
			body: formData
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
			console.error('Server transcription error:', errorData);
			throw new Error(`Server transcription error: ${errorData.error?.message || response.statusText}`);
		}

		const result = await response.json();
		return result.text || result.transcription || '';
	} catch (error) {
		console.error('Transcription error:', error);
		throw new Error('Failed to transcribe audio. Please try again.');
	}
}

export const speechApi = {
	/**
	 * Transcribe audio blob to text using OpenAI Whisper
	 */
	async transcribe(audioBlob: Blob): Promise<string> {
		return await transcribeWithWhisper(audioBlob);
	}
};
