import { OPENAI_API_KEY } from '$env/static/private';

export class OpenAIService {
	private apiKey: string;
	private baseUrl = 'https://api.openai.com/v1';

	constructor() {
		this.apiKey = OPENAI_API_KEY || '';
	}

	async generateResponse(prompt: string, includeCharts = false, includeCode = false): Promise<string> {
		try {
			let systemPrompt = `You are a helpful AI assistant. Respond in a clear and informative manner.`;
			
			if (includeCharts) {
				systemPrompt += ` When appropriate, include chart visualizations using the format:
<chart>
{
  "type": "bar|line|pie",
  "title": "Chart Title",
  "data": [
    {"label": "Category 1", "value": 10},
    {"label": "Category 2", "value": 20}
  ],
  "options": {
    "responsive": true,
    "plugins": {
      "legend": {"display": true}
    }
  }
}
</chart>`;
			}

			if (includeCode) {
				systemPrompt += ` When providing code examples, use proper markdown code blocks with language specification.`;
			}

			const response = await fetch(`${this.baseUrl}/chat/completions`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${this.apiKey}`
				},
				body: JSON.stringify({
					model: 'gpt-4',
					messages: [
						{
							role: 'system',
							content: systemPrompt
						},
						{
							role: 'user',
							content: prompt
						}
					],
					max_tokens: 2000,
					temperature: 0.7
				})
			});

			if (!response.ok) {
				throw new Error(`OpenAI API error: ${response.statusText}`);
			}

			const data = await response.json();
			return data.choices[0]?.message?.content || 'No response generated';
		} catch (error) {
			console.error('OpenAI API error:', error);
			return `Error generating response: ${error.message}`;
		}
	}

	async generateTestData(): Promise<string> {
		const testPrompts = [
			"Create a sample JSON data structure for a user profile",
			"Show me a Python function to calculate fibonacci numbers",
			"Generate a bar chart showing monthly sales data",
			"Create an HTML iframe example for embedding a video"
		];

		const randomPrompt = testPrompts[Math.floor(Math.random() * testPrompts.length)];
		return this.generateResponse(randomPrompt, true, true);
	}
}
