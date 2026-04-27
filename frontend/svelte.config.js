import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),
	kit: {
		// Use Node.js adapter for production deployment
		adapter: adapter({
			out: 'build'
		}),
		alias: {
			"@/*": "./src/lib/*"
		},
		csp: {
			mode: 'auto',
			directives: {
				'default-src': ['self'],
				'script-src': ['self', 'unsafe-inline', 'unsafe-eval'],
				'style-src': ['self', 'unsafe-inline', 'https://fonts.googleapis.com'],
				'img-src': ['self', 'data:', 'https:'],
				'font-src': ['self', 'data:', 'https://fonts.gstatic.com'],
				'connect-src': ['self', 'https://api.openai.com', 'https://mospi.edubildai.com', 'https://mospiapi.edubildai.com', 'https://statsdoc.ai.mospi.gov.in', 'http://103.48.43.155', 'https://103.48.43.155'],
				'frame-ancestors': ['none'],
				'base-uri': ['self'],
				'form-action': ['self']
			}
		}
	}
};

export default config;
