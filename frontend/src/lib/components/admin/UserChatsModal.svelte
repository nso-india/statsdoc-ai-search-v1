<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { goto } from '$app/navigation';
	import Modal from '$lib/components/common/Modal.svelte';
	import { Input } from '$lib/components/ui/input';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import X from 'lucide-svelte/icons/x';
	import Trash2 from 'lucide-svelte/icons/trash-2';
	import MessageSquare from 'lucide-svelte/icons/message-square';
	import Search from 'lucide-svelte/icons/search';
	import Eye from 'lucide-svelte/icons/eye';

	const dispatch = createEventDispatcher();

	export let show = false;
	export let user: any = null;
	export let chats: any[] = [];
	export let loading = false;

	let searchQuery = '';
	let filteredChats: any[] = [];

	$: if (chats && searchQuery !== undefined) {
		filteredChats = chats.filter(chat =>
			chat.title.toLowerCase().includes(searchQuery.toLowerCase())
		);
	}

	function formatChatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return (
			date.toLocaleDateString('en-US', {
				year: 'numeric',
				month: 'short',
				day: 'numeric'
			}) +
			' ' +
			date.toLocaleTimeString('en-US', {
				hour: 'numeric',
				minute: '2-digit',
				hour12: true
			})
		);
	}

	function deleteChat(chatId: string | number) {
		if (!confirm('Are you sure you want to delete this chat?')) {
			return;
		}
		
		dispatch('deleteChat', { chatId });
		// Don't show success toast here - let parent handle it after API call
	}

	function viewChatMessages(chatId: string | number) {		
		// Navigate to the chat view page with user ID parameter for admin access
		const userId = user?.id;
		if (userId) {
			goto(`/chat/view/${chatId}?user=${userId}`);
		} else {
			goto(`/chat/view/${chatId}`);
		}
	}	$: if (show && chats) {
		filteredChats = [...chats];
		searchQuery = '';
	}
</script>

<Modal size="lg" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
			<div class="text-lg font-medium self-center flex items-center space-x-2">
				<MessageSquare class="size-5" />
				<span>{user?.username || 'User'}'s Chats</span>
			</div>
			<Button
				variant="ghost"
				size="icon"
				class="self-center"
				onclick={() => {
					show = false;
				}}
			>
					<X class="size-5" />
			</Button>
		</div>

		<div class="flex flex-col w-full px-4 pb-3 dark:text-gray-200">
			<!-- Search -->
			<div class="mb-4">
				<div class="relative">
					<Search class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 size-4" />
					<Input
						type="text"
						placeholder="Search chats..."
						bind:value={searchQuery}
						class="pl-10 w-full"
					/>
				</div>
			</div>

			<!-- Chat List -->
			<div class="h-96 w-full overflow-y-auto border rounded-lg">
				{#if loading}
					<div class="text-center py-8 text-gray-500">
						<div class="flex flex-col items-center space-y-3">
							<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-500"></div>
							<p>Loading chats...</p>
						</div>
					</div>
				{:else if filteredChats.length === 0}
					<div class="text-center py-8 text-gray-500">
						{#if searchQuery}
							No chats found matching "{searchQuery}"
						{:else}
							No chats found for this user
						{/if}
					</div>
				{:else}
					<div class="space-y-2 p-2">
						{#each filteredChats as chat (chat.id)}
							<div
								class="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
							>
								<div class="flex-1 min-w-0">
									<h4 class="text-sm font-medium truncate">{chat.title}</h4>
									<p class="text-xs text-gray-500 mt-1">
										{formatChatDate(chat.updated_at)}
									</p>
								</div>
								<div class="flex items-center space-x-2 ml-4">
									<Button
										onclick={() => viewChatMessages(chat.id)}
										variant="ghost"
										size="icon"
										class="p-1 text-black hover:text-gray-700 hover:bg-gray-50 dark:text-white dark:hover:bg-gray-800 rounded"
										title="View Messages"
									>
											<Eye class="size-4" />
									</Button>
									<Button
										onclick={() => deleteChat(chat.id)}
										variant="ghost"
										size="icon"
										class="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
										title="Delete Chat"
									>
											<Trash2 class="size-4" />
									</Button>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="flex justify-between items-center pt-3 mt-3 border-t border-gray-200 dark:border-gray-700">
				<p class="text-xs text-gray-500">
					{filteredChats.length} chat{filteredChats.length !== 1 ? 's' : ''} found
				</p>
				<Button
					onclick={() => {
						show = false;
					}}
					variant="outline"
					class="px-3 py-1 text-sm"
				>
						Close
				</Button>
			</div>
		</div>
	</div>
</Modal>
