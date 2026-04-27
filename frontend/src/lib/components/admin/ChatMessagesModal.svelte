<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import X from 'lucide-svelte/icons/x';
	import MessageSquare from 'lucide-svelte/icons/message-square';
	import User from 'lucide-svelte/icons/user';
	import Bot from 'lucide-svelte/icons/bot';

	const dispatch = createEventDispatcher();

	export let show = false;
	export let chat: any = null;
	export let messages: any[] = [];
	export let loading = false;
	export let user: any = null;

	function formatMessageDate(dateStr: string): string {
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

	function formatMessageContent(content: any): string {
		if (typeof content === 'string') {
			return content;
		}
		if (typeof content === 'object' && content !== null) {
			// Handle structured content (e.g., with files)
			if (content.content) {
				return content.content;
			}
			// Try to extract meaningful text from object
			return JSON.stringify(content, null, 2);
		}
		return String(content);
	}

	function hasFiles(content: any): boolean {
		return typeof content === 'object' && content !== null && Array.isArray(content.files) && content.files.length > 0;
	}

	function getFiles(content: any): any[] {
		if (hasFiles(content)) {
			return content.files;
		}
		return [];
	}
</script>

<Modal size="xl" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
			<div class="text-lg font-medium self-center flex items-center space-x-2">
				<MessageSquare class="size-5" />
				<span>Chat Messages</span>
				{#if chat}
					<Badge variant="secondary" class="text-xs">
						Chat #{chat.id}
					</Badge>
				{/if}
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
			<!-- Chat Info -->
			{#if chat && user}
				<div class="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
					<div class="flex items-center justify-between">
						<div>
							<h3 class="font-medium">{chat.title}</h3>
							<p class="text-sm text-gray-500">
								by {user.username} • Created {formatMessageDate(chat.created_at)}
							</p>
						</div>
						<Badge variant="outline" class="text-xs">
							{messages.length} messages
						</Badge>
					</div>
				</div>
			{/if}

			<!-- Messages List -->
			<div class="h-96 w-full overflow-y-auto border rounded-lg">
				{#if loading}
					<div class="text-center py-8 text-gray-500">
						<div class="flex flex-col items-center space-y-3">
							<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-500"></div>
							<p>Loading messages...</p>
						</div>
					</div>
				{:else if messages.length === 0}
					<div class="text-center py-8 text-gray-500">
						No messages found in this chat
					</div>
				{:else}
					<div class="space-y-4 p-4">
						{#each messages as message (message.id)}
							<div class="flex space-x-3">
								<div class="flex-shrink-0">
									{#if message.role === 'user'}
										<div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
											<User class="size-4 text-white" />
										</div>
									{:else}
										<div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
											<Bot class="size-4 text-white" />
										</div>
									{/if}
								</div>
								<div class="flex-1 min-w-0">
									<div class="flex items-center space-x-2 mb-1">
										<Badge variant={message.role === 'user' ? 'default' : 'secondary'} class="text-xs">
											{message.role === 'user' ? 'User' : 'Assistant'}
										</Badge>
										<span class="text-xs text-gray-500">
											{formatMessageDate(message.created_at)}
										</span>
									</div>
									<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 message-content">
										<div class="whitespace-pre-wrap text-sm">
											{formatMessageContent(message.content)}
										</div>
										
										<!-- Files if present -->
										{#if hasFiles(message.content)}
											<div class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
												<div class="text-xs text-gray-500 mb-2">Attached Files:</div>
												<div class="space-y-1">
													{#each getFiles(message.content) as file}
														<div class="flex items-center space-x-2 text-xs bg-blue-50 dark:bg-blue-900/20 p-2 rounded">
															<span class="font-medium">📎</span>
															<span>{file.file_name || file.name || 'Unknown file'}</span>
															{#if file.id}
																<Badge variant="outline" class="text-xs">ID: {file.id}</Badge>
															{/if}
														</div>
													{/each}
												</div>
											</div>
										{/if}
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="flex justify-between items-center pt-3 mt-3 border-t border-gray-200 dark:border-gray-700">
				<p class="text-xs text-gray-500">
					{messages.length} message{messages.length !== 1 ? 's' : ''} in this chat
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

<style>
	.message-content {
		max-width: 100%;
		word-wrap: break-word;
		overflow-wrap: break-word;
	}
</style>
