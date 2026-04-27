/**
 * SvelteKit Server Hooks
 * 
 * Security Headers Implementation (CWE-493, CWE-200, CWE-1021)
 * These headers are added at the application level for defense-in-depth
 * alongside NGINX headers.
 */

import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	const response = await resolve(event);

	// Security Headers - Applied to all responses
	
	// Prevent MIME-sniffing
	response.headers.set('X-Content-Type-Options', 'nosniff');
	
// Prevent clickjacking (allow same-origin framing so in-app iframes can work)
	response.headers.set('X-Frame-Options', 'SAMEORIGIN');
	
	// Legacy XSS protection for older browsers
	response.headers.set('X-XSS-Protection', '1; mode=block');
	
	// Control referrer information
	response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
	
	// Restrict browser features (only essential restrictions)
	response.headers.set(
		'Permissions-Policy',
		'geolocation=(), microphone=(self), camera=(), payment=()'
	);
	
	// Content Security Policy (if not already set by SvelteKit's CSP config)
	if (!response.headers.has('Content-Security-Policy')) {
		response.headers.set(
			'Content-Security-Policy',
			"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https:; font-src 'self' data: https://fonts.gstatic.com; connect-src 'self' https://api.openai.com https://mospi.edubildai.com https://mospiapi.edubildai.com https://statsdoc.ai.mospi.gov.in http://103.48.43.155 https://103.48.43.155; frame-ancestors 'self'; base-uri 'self'; form-action 'self';"
		);
	}
	
	// Strict Transport Security (HSTS) - Enforce HTTPS
	// Note: This should primarily be set by NGINX, but adding here for completeness
	response.headers.set(
		'Strict-Transport-Security',
		'max-age=31536000; includeSubDomains; preload'
	);

	return response;
};
