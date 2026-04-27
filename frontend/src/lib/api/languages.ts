import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface Language {
	id: string;
	code: string;
	name: string;
	display_order: number;
}

/**
 * Fetch all active languages from the backend
 */
export async function getLanguages(): Promise<Language[]> {
    try {
        const response = await fetch(`${WEBUI_API_BASE_URL}/chat/languages/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch languages: ${response.statusText}`);
        }

        const languages: Language[] = await response.json();
        return languages;
    } catch (error) {
		console.error('Error fetching languages:', error);
		// Fallback to default language
		return [
			{
				id: 'default-en',
				code: 'en',
				name: 'English',
				display_order: 1
			}
		];
	}
}
