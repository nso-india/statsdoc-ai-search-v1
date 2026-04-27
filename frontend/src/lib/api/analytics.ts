import { WEBUI_API_BASE_URL } from '$lib/constants/app';

export async function getAnalyticsDashboard(token: string, days: number = 30) {
    const response = await fetch(
        `${WEBUI_API_BASE_URL}/chat/analytics/dashboard/?days=${days}`,
        {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }
    );

    if (!response.ok) {
        throw new Error('Failed to fetch analytics data');
    }

    return response.json();
}

export async function getChatSessionDetail(token: string, chatId: number) {
    const response = await fetch(
        `${WEBUI_API_BASE_URL}/chats/analytics/chat/${chatId}/`,
        {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }
    );

    if (!response.ok) {
        throw new Error('Failed to fetch chat session details');
    }

    return response.json();
}
