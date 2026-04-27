// Authentication types following Open WebUI pattern
export interface LoginRequest {
	username: string;
	password: string;
}

export interface LoginResponse {
	access: string;
	refresh: string;
	user: User;
}

export interface TokenRefreshRequest {
	refresh: string;
}

export interface TokenRefreshResponse {
	access: string;
}

export interface User {
	id: number;
	username: string;
	email: string;
	first_name?: string;
	last_name?: string;
	is_active?: boolean;
	is_staff?: boolean;
	is_superuser?: boolean;
	role?: 'SUPERADMIN' | 'STAFF' | 'USER';
	access_level?: number;
	date_joined?: string;
	last_login?: string;
}

export interface AuthState {
	isAuthenticated: boolean;
	user: User | null;
	token: string | null;
	refreshToken: string | null;
}

export interface AuthStore extends AuthState {
	login: (credentials: LoginRequest) => Promise<void>;
	logout: () => void;
	refresh: () => Promise<void>;
	updateUser: (user: Partial<User>) => void;
}

// File-related types following Open WebUI pattern
export interface UploadedFile {
	id: number;
	file: string;
	file_name: string;
	uploaded_at: string;
	other_info?: any;
	status: string;
	docling_json?: any;
}

export interface FileItem {
	id: number;
	file_name: string;
	uploaded_at: string;
	status: string;
	approve_status?: string;
}

export interface FileUploadRequest {
	file: File;
	other_info?: any;
}

export interface FileUploadResponse {
	id: number;
	file: string;
	file_name: string;
	uploaded_at: string;
	other_info?: any;
	status: string;
	docling_json?: any;
}

export interface MultiFileUploadResponse {
	success: FileUploadResponse[];
	errors?: any[];
}

export interface ProcessingJob {
	id: string;
	status: 'pending' | 'processing' | 'completed' | 'failed';
	file_id: number;
	created_at: string;
	completed_at?: string;
	result?: any;
	error?: string;
}

export interface ExtractedContent {
	text: string;
	metadata: Record<string, any>;
	structure?: any;
}

// UI-related types following Open WebUI pattern
export interface ToastMessage {
	id: string;
	type: 'success' | 'error' | 'warning' | 'info';
	title: string;
	message?: string;
	duration?: number;
	dismissible?: boolean;
}

export interface ModalProps {
	isOpen: boolean;
	title?: string;
	size?: 'sm' | 'md' | 'lg' | 'xl';
	closable?: boolean;
	onClose?: () => void;
}

export interface LoadingState {
	isLoading: boolean;
	message?: string;
	progress?: number;
}

export interface SidebarState {
	isOpen: boolean;
	isCollapsed: boolean;
	activeSection?: string;
}

export interface TableColumn<T = any> {
	key: keyof T;
	label: string;
	sortable?: boolean;
	width?: string;
	align?: 'left' | 'center' | 'right';
	render?: (value: any, row: T) => string;
}

export interface PaginationState {
	page: number;
	pageSize: number;
	total: number;
	totalPages: number;
}

// User-related types following Open WebUI pattern
export interface UserProfile {
	username: string;
	email: string;
	first_name?: string;
	last_name?: string;
	avatar?: string;
	bio?: string;
	preferences?: UserPreferences;
}

export interface UserPreferences {
	theme: 'light' | 'dark' | 'system';
	language: string;
	notifications: NotificationSettings;
	display: DisplaySettings;
}

export interface NotificationSettings {
	email: boolean;
	push: boolean;
	file_processing: boolean;
	system_updates: boolean;
}

export interface DisplaySettings {
	items_per_page: number;
	show_file_previews: boolean;
	auto_refresh: boolean;
}

// API Response types following Open WebUI pattern
export interface ApiResponse<T = any> {
	success: boolean;
	data?: T;
	error?: string;
	message?: string;
}

export interface PaginatedResponse<T = any> {
	results: T[];
	count: number;
	next?: string;
	previous?: string;
}

// Theme types following Open WebUI pattern
export type Theme = 'light' | 'dark' | 'system';

// Banner types following Open WebUI pattern (like Open WebUI)
export interface Banner {
	id: string;
	type: string;
	title?: string;
	content: string;
	url?: string;
	dismissible?: boolean;
	timestamp: number;
}

// Enums following Open WebUI pattern
export enum FileStatus {
	PENDING = 'pending',
	PROCESSING = 'processing', 
	COMPLETED = 'completed',
	FAILED = 'failed',
	CANCELLED = 'cancelled'
}