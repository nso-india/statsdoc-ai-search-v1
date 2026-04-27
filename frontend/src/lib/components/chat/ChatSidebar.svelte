<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let chats: Array<{
		id: number;
		title: string;
		created_at: string;
		updated_at: string;
		message_count: number;
		last_message?: any;
	}> = [];
	export let currentChatId: number | null = null;

	const dispatch = createEventDispatcher();

	function selectChat(chat: any) {
		dispatch('selectChat', chat);
	}

	function newChat() {
		dispatch('newChat');
	}

	function deleteChat(chatId: number, event: Event) {
		event.stopPropagation();
		if (confirm('Are you sure you want to delete this chat?')) {
			dispatch('deleteChat', chatId);
		}
	}

	function closeSidebar() {
		dispatch('closeSidebar');
	}

	function formatDate(dateString: string) {
		const date = new Date(dateString);
		const now = new Date();
		const diffTime = Math.abs(now.getTime() - date.getTime());
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

		if (diffDays === 1) return 'Today';
		if (diffDays === 2) return 'Yesterday';
		if (diffDays <= 7) return `${diffDays - 1} days ago`;
		return date.toLocaleDateString();
	}

	function truncateTitle(title: string, maxLength = 30) {
		return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
	}
</script>

<div class="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
	<!-- Header -->
	<div class="p-4 border-b border-gray-200">
		<div class="flex items-center justify-between">
			<div class="flex items-center">
				<img 
					src="/MOSPILOGO.webp" 
					alt="MOSPI Logo" 
					class="h-8 w-8 mr-2" 
				/>
					<div class="flex flex-col leading-tight">
						<span class="text-sm font-semibold">MoSPI StatsDoc AI Assistantβeta</span>
						<span class="text-xs text-gray-500">MOSPI</span>
					</div>
			</div>
			<button
				on:click={closeSidebar}
				class="p-1 text-gray-400 hover:text-gray-600 lg:hidden"
				aria-label="Close sidebar"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>
		
		<button
			on:click={newChat}
			class="w-full mt-3 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
		>
			New Chat
		</button>
	</div>

	<!-- Chat List -->
	<div class="flex-1 overflow-y-auto">
		{#if chats.length === 0}
			<div class="p-4 text-center text-gray-500">
				<svg class="w-12 h-12 mx-auto text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-4.646-1.297l-5.823 2.259a.5.5 0 01-.777-.416V9.534c0-4.418 3.582-8 8-8s8 3.582 8 8z" />
				</svg>
				<p class="text-sm">No chats yet</p>
				<p class="text-xs text-gray-400">Start a new conversation</p>
			</div>
		{:else}
			<div class="p-2">
				{#each chats as chat (chat.id)}
					<div
						class="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors group relative {currentChatId === chat.id ? 'bg-blue-50 border border-blue-200' : ''}"
					>
						<div class="flex items-start justify-between">
							<button
								on:click={() => selectChat(chat)}
								class="flex-1 min-w-0 text-left"
							>
								<h3 class="text-sm font-medium text-gray-900 truncate">
									{truncateTitle(chat.title)}
								</h3>
								
								{#if chat.last_message}
									<p class="text-xs text-gray-500 truncate mt-1">
										{truncateTitle(chat.last_message.content, 50)}
									</p>
								{/if}
								
								<div class="flex items-center mt-2 text-xs text-gray-400">
									<span>{formatDate(chat.updated_at)}</span>
									<span class="mx-1">•</span>
									<span>{chat.message_count} messages</span>
								</div>
							</button>
							
							<button
								on:click={(e) => deleteChat(chat.id, e)}
								class="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
								aria-label="Delete chat"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Footer -->
	<div class="p-4 border-t border-gray-200">
		<div class="text-xs text-gray-500 text-center">
			MOSPI Chat Interface
		</div>
	</div>
</div>

<style>
	/* Custom scrollbar */
	div::-webkit-scrollbar {
		width: 6px;
	}
	
	div::-webkit-scrollbar-track {
		background: #f1f1f1;
	}
	
	div::-webkit-scrollbar-thumb {
		background: #162f6a;
		border-radius: 3px;
	}
	
	div::-webkit-scrollbar-thumb:hover {
		background: #1a3575;
	}
</style>
