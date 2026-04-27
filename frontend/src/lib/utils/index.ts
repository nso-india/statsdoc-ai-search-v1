import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { cubicOut, quartOut, quintOut } from "svelte/easing";
import type { TransitionConfig } from "svelte/transition";
import { WEBUI_BASE_URL } from '$lib/constants';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

// Enhanced animation system for smooth interactions
type FlyAndScaleParams = {
	y?: number;
	x?: number;
	start?: number;
	duration?: number;
};

export const flyAndScale = (
	node: Element,
	params: FlyAndScaleParams = { y: -8, x: 0, start: 0.95, duration: 200 }
): TransitionConfig => {
	const style = getComputedStyle(node);
	const transform = style.transform === "none" ? "" : style.transform;

	const scaleConversion = (
		valueA: number,
		scaleA: [number, number],
		scaleB: [number, number]
	) => {
		const [minA, maxA] = scaleA;
		const [minB, maxB] = scaleB;

		const percentage = (valueA - minA) / (maxA - minA);
		const valueB = percentage * (maxB - minB) + minB;

		return valueB;
	};

	const styleToString = (
		style: Record<string, number | string | undefined>
	): string => {
		return Object.keys(style).reduce((str, key) => {
			if (style[key] === undefined) return str;
			return str + `${key}:${style[key]};`;
		}, "");
	};

	return {
		duration: params.duration ?? 200,
		delay: 0,
		css: (t) => {
			const y = scaleConversion(t, [0, 1], [params.y ?? -8, 0]);
			const x = scaleConversion(t, [0, 1], [params.x ?? 0, 0]);
			const scale = scaleConversion(t, [0, 1], [params.start ?? 0.95, 1]);

			return styleToString({
				transform: `${transform} translate3d(${x}px, ${y}px, 0) scale(${scale})`,
				opacity: t
			});
		},
		easing: cubicOut
	};
};

// Smooth slide transition for smooth page/component transitions
export const smoothSlide = (
	node: Element,
	{ duration = 300, easing = quartOut, axis = 'y' } = {}
): TransitionConfig => {
	const style = getComputedStyle(node);
	const opacity = +style.opacity;
	const primary_property = axis === 'y' ? 'height' : 'width';
	const primary_property_value = parseFloat(style[primary_property]);
	const secondary_properties = axis === 'y' ? ['top', 'bottom'] : ['left', 'right'];
	const capitalized_secondary_properties = secondary_properties.map(
		(property) => `${property[0].toUpperCase()}${property.slice(1)}`
	);
	const padding_start_value = parseFloat(style[`padding${capitalized_secondary_properties[0]}`]);
	const padding_end_value = parseFloat(style[`padding${capitalized_secondary_properties[1]}`]);
	const margin_start_value = parseFloat(style[`margin${capitalized_secondary_properties[0]}`]);
	const margin_end_value = parseFloat(style[`margin${capitalized_secondary_properties[1]}`]);
	const border_width_start_value = parseFloat(
		style[`border${capitalized_secondary_properties[0]}Width`]
	);
	const border_width_end_value = parseFloat(
		style[`border${capitalized_secondary_properties[1]}Width`]
	);

	return {
		duration,
		easing,
		css: (t) =>
			'overflow: hidden;' +
			`opacity: ${Math.min(t * 20, 1) * opacity};` +
			`${primary_property}: ${t * primary_property_value}px;` +
			`padding-${secondary_properties[0]}: ${t * padding_start_value}px;` +
			`padding-${secondary_properties[1]}: ${t * padding_end_value}px;` +
			`margin-${secondary_properties[0]}: ${t * margin_start_value}px;` +
			`margin-${secondary_properties[1]}: ${t * margin_end_value}px;` +
			`border-${secondary_properties[0]}-width: ${t * border_width_start_value}px;` +
			`border-${secondary_properties[1]}-width: ${t * border_width_end_value}px;`
	};
};

// Smooth fade transition for content changes
export const smoothFade = (
	node: Element,
	{ duration = 150, easing = cubicOut } = {}
): TransitionConfig => {
	return {
		duration,
		easing,
		css: (t) => `opacity: ${t}; transform: translateY(${(1 - t) * 10}px);`
	};
};

// Smooth scale transition for modals and dropdowns
export const smoothScale = (
	node: Element,
	{ duration = 200, start = 0.9, easing = quintOut } = {}
): TransitionConfig => {
	return {
		duration,
		easing,
		css: (t) => {
			const scale = start + (1 - start) * t;
			return `transform: scale(${scale}); opacity: ${t};`;
		}
	};
};

// Smooth blur transition for backgrounds
export const smoothBlur = (
	node: Element,
	{ duration = 300, amount = 5, easing = cubicOut } = {}
): TransitionConfig => {
	return {
		duration,
		easing,
		css: (t) => `filter: blur(${(1 - t) * amount}px); opacity: ${0.3 + t * 0.7};`
	};
};

// Button press animation utility
export const createButtonPress = (node: Element) => {
	const handleMouseDown = () => {
		node.style.transform = 'scale(0.98)';
		node.style.transition = 'transform 0.1s ease-out';
	};

	const handleMouseUp = () => {
		node.style.transform = 'scale(1)';
		node.style.transition = 'transform 0.15s ease-out';
	};

	const handleMouseLeave = () => {
		node.style.transform = 'scale(1)';
		node.style.transition = 'transform 0.15s ease-out';
	};

	node.addEventListener('mousedown', handleMouseDown);
	node.addEventListener('mouseup', handleMouseUp);
	node.addEventListener('mouseleave', handleMouseLeave);
	node.addEventListener('touchstart', handleMouseDown);
	node.addEventListener('touchend', handleMouseUp);

	return {
		destroy() {
			node.removeEventListener('mousedown', handleMouseDown);
			node.removeEventListener('mouseup', handleMouseUp);
			node.removeEventListener('mouseleave', handleMouseLeave);
			node.removeEventListener('touchstart', handleMouseDown);
			node.removeEventListener('touchend', handleMouseUp);
		}
	};
};

// Smooth loading states
export const createLoadingState = () => {
	let isLoading = false;
	let loadingTimeout: NodeJS.Timeout;

	const setLoading = (loading: boolean, minDelay = 150) => {
		if (loading) {
			isLoading = true;
		} else {
			// Ensure loading state shows for at least minDelay ms for smooth UX
			loadingTimeout = setTimeout(() => {
				isLoading = false;
			}, minDelay);
		}
		return isLoading;
	};

	const cleanup = () => {
		if (loadingTimeout) clearTimeout(loadingTimeout);
	};

	return { setLoading, cleanup };
};

//////////////////////////
// Helper functions following Open WebUI pattern
//////////////////////////

export const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Date formatting utilities following Open WebUI pattern
export const formatDate = (inputDate: Date | string) => {
	const date = typeof inputDate === 'string' ? new Date(inputDate) : inputDate;
	const now = new Date();

	if (isToday(date)) {
		return `Today at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
	} else if (isYesterday(date)) {
		return `Yesterday at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
	} else {
		return `${date.toLocaleDateString()} at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
	}
};

export const formatDateToIST = (date: string | Date): string => {
	const dateObj = typeof date === 'string' ? new Date(date) : date;
	
	// Convert to IST (India Standard Time)
	const istOptions: Intl.DateTimeFormatOptions = {
		timeZone: 'Asia/Kolkata',
		year: 'numeric',
		month: 'short',
		day: 'numeric',
		hour: '2-digit',
		minute: '2-digit',
		hour12: true
	};
	
	return dateObj.toLocaleDateString('en-IN', istOptions);
};

export const formatTimeAgo = (date: Date | string): string => {
	const dateObj = typeof date === 'string' ? new Date(date) : date;
	const now = new Date();
	const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);

	if (diffInSeconds < 60) return 'just now';
	if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
	if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
	if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
	if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)} months ago`;
	return `${Math.floor(diffInSeconds / 31536000)} years ago`;
};

export const isToday = (date: Date | string): boolean => {
	const dateObj = typeof date === 'string' ? new Date(date) : date;
	const today = new Date();
	return dateObj.toDateString() === today.toDateString();
};

export const isYesterday = (date: Date | string): boolean => {
	const dateObj = typeof date === 'string' ? new Date(date) : date;
	const yesterday = new Date();
	yesterday.setDate(yesterday.getDate() - 1);
	return dateObj.toDateString() === yesterday.toDateString();
};

// File utilities following Open WebUI pattern
export const formatFileSize = (bytes: number): string => {
	if (bytes == null) return 'Unknown size';
	if (typeof bytes !== 'number' || bytes < 0) return 'Invalid size';
	if (bytes === 0) return '0 B';
	const units = ['B', 'KB', 'MB', 'GB', 'TB'];
	let unitIndex = 0;

	while (bytes >= 1024 && unitIndex < units.length - 1) {
		bytes /= 1024;
		unitIndex++;
	}
	return `${bytes.toFixed(1)} ${units[unitIndex]}`;
};

export const getFileExtension = (filename: string): string => {
	return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
};

export const getFileName = (filename: string): string => {
	return filename.replace(/\.[^/.]+$/, '');
};

export const transformFileName = (fileName: string) => {
	// Convert to lowercase
	const lowerCaseFileName = fileName.toLowerCase();
	// Remove special characters using regular expression
	const sanitizedFileName = lowerCaseFileName.replace(/[^\w\s]/g, '');
	// Replace spaces with dashes
	const finalFileName = sanitizedFileName.replace(/\s+/g, '-');
	return finalFileName;
};

export const downloadFile = (blob: Blob, filename: string): void => {
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	URL.revokeObjectURL(url);
};

// Text formatting utilities following Open WebUI pattern
export const capitalizeFirstLetter = (string: string) => {
	return string.charAt(0).toUpperCase() + string.slice(1);
};

export const slugify = (str: string): string => {
	return (
		str
			// 1. Normalize: separate accented letters into base + combining marks
			.normalize('NFD')
			// 2. Remove all combining marks (the accents)
			.replace(/[\u0300-\u036f]/g, '')
			// 3. Replace any sequence of whitespace with a single hyphen
			.replace(/\s+/g, '-')
			// 4. Remove all characters except alphanumeric characters and hyphens
			.replace(/[^a-zA-Z0-9-]/g, '')
			// 5. Convert to lowercase
			.toLowerCase()
	);
};

export const truncateText = (text: string, maxLength: number): string => {
	if (text.length <= maxLength) return text;
	return text.slice(0, maxLength) + '...';
};

// Clipboard utilities following Open WebUI pattern
export const copyToClipboard = async (text: string, showToast: boolean = true) => {
	let result = false;
	if (!navigator.clipboard) {
		const textArea = document.createElement('textarea');
		textArea.value = text;
		// Avoid scrolling to bottom
		textArea.style.top = '0';
		textArea.style.left = '0';
		textArea.style.position = 'fixed';

		document.body.appendChild(textArea);
		textArea.focus();
		textArea.select();

		try {
			const successful = document.execCommand('copy');
			console.log('Fallback: Copying text command was ' + (successful ? 'successful' : 'unsuccessful'));
			result = successful;
			if (showToast && successful) {
				// For environments where toast is available, import dynamically
				try {
					const { toast } = await import('svelte-sonner');
					toast.success('Copied to clipboard successfully!');
				} catch (e) {
					console.log('Toast not available');
				}
			}
		} catch (err) {
			console.error('Fallback: Oops, unable to copy', err);
			if (showToast) {
				try {
					const { toast } = await import('svelte-sonner');
					toast.error('Failed to copy to clipboard');
				} catch (e) {
					console.log('Toast not available');
				}
			}
		}

		document.body.removeChild(textArea);
		return result;
	}

	result = await navigator.clipboard
		.writeText(text)
		.then(() => {
			console.log('Async: Copying to clipboard was successful!');
			if (showToast) {
				// For environments where toast is available, import dynamically
				import('svelte-sonner').then(({ toast }) => {
					toast.success('Copied to clipboard successfully!');
				}).catch(() => {
					console.log('Toast not available');
				});
			}
			return true;
		})
		.catch((error) => {
			console.error('Async: Could not copy text: ', error);
			if (showToast) {
				import('svelte-sonner').then(({ toast }) => {
					toast.error('Failed to copy to clipboard');
				}).catch(() => {
					console.log('Toast not available');
				});
			}
			return false;
		});

	return result;
};

// Validation utilities following Open WebUI pattern
export const isValidEmail = (email: string): boolean => {
	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	return emailRegex.test(email);
};

export const isValidHttpUrl = (string: string) => {
	let url;
	try {
		url = new URL(string);
	} catch (_) {
		return false;
	}
	return url.protocol === 'http:' || url.protocol === 'https:';
};

export const isValidPassword = (password: string): boolean => {
	// At least 8 characters, 1 uppercase, 1 lowercase, 1 number
	const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
	return passwordRegex.test(password);
};

export const isValidUsername = (username: string): boolean => {
	// 3-20 characters, alphanumeric and underscores only
	const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
	return usernameRegex.test(username);
};

// Storage utilities following Open WebUI pattern
export const setLocalStorageItem = (key: string, value: any): void => {
	try {
		if (typeof window !== 'undefined') {
			localStorage.setItem(key, JSON.stringify(value));
		}
	} catch (error) {
		console.warn('Failed to save to localStorage:', error);
	}
};

export const getLocalStorageItem = <T = any>(key: string): T | null => {
	try {
		if (typeof window !== 'undefined') {
			const item = localStorage.getItem(key);
			return item ? JSON.parse(item) : null;
		}
	} catch (error) {
		console.warn('Failed to read from localStorage:', error);
	}
	return null;
};

export const removeLocalStorageItem = (key: string): void => {
	try {
		if (typeof window !== 'undefined') {
			localStorage.removeItem(key);
		}
	} catch (error) {
		console.warn('Failed to remove from localStorage:', error);
	}
};

// Number formatting utilities following Open WebUI pattern
export const formatNumber = (num: number): string => {
	return new Intl.NumberFormat().format(num);
};

export const formatCurrency = (amount: number, currency = 'USD'): string => {
	return new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency
	}).format(amount);
};

export const formatPercentage = (value: number, decimals = 1): string => {
	return `${(value * 100).toFixed(decimals)}%`;
};

// Time utilities following Open WebUI pattern
export const getCurrentDateTime = () => {
	return `${getFormattedDate()} ${getFormattedTime()}`;
};

export const getFormattedDate = () => {
	const date = new Date();
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, '0');
	const day = String(date.getDate()).padStart(2, '0');
	return `${year}-${month}-${day}`;
};

export const getFormattedTime = () => {
	const date = new Date();
	return date.toTimeString().split(' ')[0];
};

export const getUserTimezone = () => {
	return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

export const getWeekday = () => {
	const date = new Date();
	const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
	return weekdays[date.getDay()];
};

// UUID and hash utilities following Open WebUI pattern
export const generateId = (): string => {
	return `id-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

export const generateFileId = (): string => {
	return `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// File reading utilities following Open WebUI pattern
export const readFileAsText = (file: File): Promise<string> => {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = (e) => resolve(e.target?.result as string);
		reader.onerror = (e) => reject(e);
		reader.readAsText(file);
	});
};

export const readFileAsDataURL = (file: File): Promise<string> => {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = (e) => resolve(e.target?.result as string);
		reader.onerror = (e) => reject(e);
		reader.readAsDataURL(file);
	});
};

// Storage availability check following Open WebUI pattern
export const isStorageAvailable = (): boolean => {
	try {
		if (typeof window === 'undefined') return false;
		const test = '__storage_test__';
		localStorage.setItem(test, test);
		localStorage.removeItem(test);
		return true;
	} catch {
		return false;
	}
};

// Template processing utilities following Open WebUI pattern
export const promptTemplate = (
	template: string,
	user_name?: string,
	user_location?: string
): string => {
	// Get the current date
	const currentDate = new Date();

	// Format the date to YYYY-MM-DD
	const formattedDate =
		currentDate.getFullYear() +
		'-' +
		String(currentDate.getMonth() + 1).padStart(2, '0') +
		'-' +
		String(currentDate.getDate()).padStart(2, '0');

	// Format the time to HH:MM:SS AM/PM
	const currentTime = currentDate.toLocaleTimeString('en-US', {
		hour: 'numeric',
		minute: 'numeric',
		second: 'numeric',
		hour12: true
	});

	// Get the current weekday
	const currentWeekday = getWeekday();

	// Get the user's timezone
	const currentTimezone = getUserTimezone();

	// Get the user's language
	const userLanguage = localStorage.getItem('locale') || 'en-US';

	// Replace {{CURRENT_DATETIME}} in the template with the formatted datetime
	template = template.replace('{{CURRENT_DATETIME}}', `${formattedDate} ${currentTime}`);

	// Replace {{CURRENT_DATE}} in the template with the formatted date
	template = template.replace('{{CURRENT_DATE}}', formattedDate);

	// Replace {{CURRENT_TIME}} in the template with the formatted time
	template = template.replace('{{CURRENT_TIME}}', currentTime);

	// Replace {{CURRENT_WEEKDAY}} in the template with the current weekday
	template = template.replace('{{CURRENT_WEEKDAY}}', currentWeekday);

	// Replace {{CURRENT_TIMEZONE}} in the template with the user's timezone
	template = template.replace('{{CURRENT_TIMEZONE}}', currentTimezone);

	// Replace {{USER_LANGUAGE}} in the template with the user's language
	template = template.replace('{{USER_LANGUAGE}}', userLanguage);

	if (user_name) {
		// Replace {{USER_NAME}} in the template with the user's name
		template = template.replace('{{USER_NAME}}', user_name);
	}

	if (user_location) {
		// Replace {{USER_LOCATION}} in the template with the current location
		template = template.replace('{{USER_LOCATION}}', user_location);
	} else {
		// Replace {{USER_LOCATION}} in the template with 'Unknown' if no location is provided
		template = template.replace('{{USER_LOCATION}}', 'LOCATION_UNKNOWN');
	}

	return template;
};