<script lang="ts">
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import { Input } from '$lib/components/ui/input';
	import { submitFeedback } from '$lib/api/feedback';
	import { user, authToken } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import X from '@lucide/svelte/icons/x';
	import MessageSquare from '@lucide/svelte/icons/message-square';
	import Paperclip from '@lucide/svelte/icons/paperclip';

	let { open = $bindable(false) } = $props();

	let name = $state('');
	let email = $state('');
	let subject = $state('');
	let message = $state('');
	let attachmentFiles = $state<File[]>([]);
	let submitting = $state(false);
	let fileInput: HTMLInputElement | undefined = $state();

	const MAX_ATTACHMENTS = 3;
	const MAX_FILE_SIZE = 2 * 1024 * 1024;
	const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/webp'];

	$effect(() => {
		if (open && $user) {
			name = $user.name || $user.username || '';
			email = $user.email || '';
		}
	});

	function resetForm() {
		if ($user) {
			name = $user.name || $user.username || '';
			email = $user.email || '';
		} else {
			name = '';
			email = '';
		}
		subject = '';
		message = '';
		attachmentFiles = [];
		if (fileInput) fileInput.value = '';
	}

	function handleClose() {
		open = false;
	}

	function addFiles(files: FileList | File[] | null | undefined) {
		if (!files) return;

		for (const file of Array.from(files)) {
			if (attachmentFiles.length >= MAX_ATTACHMENTS) {
				toast.error(`You can attach at most ${MAX_ATTACHMENTS} screenshots.`);
				break;
			}
			if (!ALLOWED_TYPES.includes(file.type)) {
				toast.error('Only PNG, JPG, and WEBP images are allowed.');
				continue;
			}
			if (file.size > MAX_FILE_SIZE) {
				toast.error(`"${file.name}" exceeds the 2 MB limit.`);
				continue;
			}
			attachmentFiles = [...attachmentFiles, file];
		}
	}

	function handleFileChange(event: Event) {
		const input = event.target as HTMLInputElement;
		addFiles(input.files);
		if (input) input.value = '';
	}

	function handlePaste(event: ClipboardEvent) {
		const items = event.clipboardData?.items;
		if (!items) return;

		const pasted: File[] = [];
		for (const item of items) {
			if (!item.type.startsWith('image/')) continue;
			const blob = item.getAsFile();
			if (!blob) continue;
			const ext = blob.type === 'image/png' ? 'png' : 'jpg';
			pasted.push(new File([blob], `pasted-screenshot-${Date.now()}.${ext}`, { type: blob.type }));
		}

		if (pasted.length > 0) {
			event.preventDefault();
			addFiles(pasted);
		}
	}

	function removeAttachment(index: number) {
		attachmentFiles = attachmentFiles.filter((_, i) => i !== index);
	}

	async function handleSubmit(event: Event) {
		event.preventDefault();

		if (!subject.trim()) {
			toast.error('Subject is required.');
			return;
		}
		if (!message.trim()) {
			toast.error('Message is required.');
			return;
		}
		if (!$user && (!name.trim() || !email.trim())) {
			toast.error('Name and email are required.');
			return;
		}

		submitting = true;
		try {
			const result = await submitFeedback({
				name: name.trim(),
				email: email.trim(),
				subject: subject.trim(),
				message: message.trim(),
				attachments: attachmentFiles,
				token: $authToken
			});
			toast.success(result.message || 'Thank you for your feedback.');
			resetForm();
			open = false;
		} catch (error) {
			toast.error(error instanceof Error ? error.message : 'Failed to submit feedback.');
		} finally {
			submitting = false;
		}
	}
</script>

<AlertDialog.Root bind:open>
	<AlertDialog.Content
		class="sm:max-w-[540px] p-0 overflow-hidden gap-0 border-0"
		oninteractoutside={() => (open = false)}
	>
		<button
			type="button"
			onclick={handleClose}
			class="absolute right-4 top-4 z-10 rounded-sm text-white/80 transition-opacity hover:text-white"
			aria-label="Close"
		>
			<X class="h-4 w-4" />
		</button>

		<div class="feedback-header px-6 py-5 text-center text-white">
			<div class="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-white">
				<MessageSquare class="h-5 w-5 text-[#1a337e]" />
			</div>
			<h2 class="text-xl font-semibold">Feedback</h2>
			<p class="mt-1 text-sm text-white/90">Help us improve your experience</p>
		</div>

		<form class="space-y-4 bg-white px-6 py-5" onsubmit={handleSubmit} onpaste={handlePaste}>
			<input type="text" name="website" tabindex="-1" autocomplete="off" class="hidden" aria-hidden="true" />

			{#if !$user}
				<div class="space-y-2">
					<label for="feedback-name" class="text-sm font-medium text-[#1f2937]">
						Name <span class="text-[#ef4444]">*</span>
					</label>
					<Input id="feedback-name" bind:value={name} placeholder="Your name" required />
				</div>
				<div class="space-y-2">
					<label for="feedback-email" class="text-sm font-medium text-[#1f2937]">
						Email <span class="text-[#ef4444]">*</span>
					</label>
					<Input id="feedback-email" type="email" bind:value={email} placeholder="you@example.com" required />
				</div>
			{/if}

			<div class="space-y-2">
				<label for="feedback-subject" class="text-sm font-medium text-[#1f2937]">
					Subject <span class="text-[#ef4444]">*</span>
				</label>
				<Input id="feedback-subject" bind:value={subject} placeholder="Brief subject" required maxlength={200} />
			</div>

			<div class="space-y-2">
				<label for="feedback-message" class="text-sm font-medium text-[#1f2937]">
					Message <span class="text-[#ef4444]">*</span>
				</label>
				<textarea
					id="feedback-message"
					bind:value={message}
					placeholder="Please share your feedback, suggestions, or issues you encountered..."
					required
					maxlength={2000}
					rows={5}
					class="border-input bg-background placeholder:text-muted-foreground focus-visible:ring-ring w-full rounded-md border px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
				></textarea>
			</div>

			<div class="space-y-2">
				<label class="text-sm font-medium text-[#1f2937]">
					Screenshot <span class="text-sm font-normal text-gray-500">(Optional)</span>
				</label>
				<p class="text-xs text-gray-500">PNG/JPG, max 2 MB each, up to 3 files. Ctrl+V to paste.</p>
				<div class="flex items-center gap-2">
					<label class="feedback-attach-btn inline-flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm">
						<Paperclip class="h-4 w-4" />
						Attach screenshot
						<input
							bind:this={fileInput}
							type="file"
							accept="image/png,image/jpeg,image/webp"
							multiple
							class="hidden"
							onchange={handleFileChange}
						/>
					</label>
				</div>
				{#if attachmentFiles.length > 0}
					<ul class="space-y-1">
						{#each attachmentFiles as file, index (file.name + index)}
							<li class="flex items-center justify-between rounded-md bg-[#f3f4f6] px-3 py-2 text-sm">
								<span class="truncate">{file.name}</span>
								<button type="button" class="text-[#1a337e] hover:underline" onclick={() => removeAttachment(index)}>
									Remove
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</div>

			<div class="flex justify-end gap-3 pt-2">
				<button
					type="button"
					class="feedback-reset-btn rounded-md px-4 py-2 text-sm font-medium"
					onclick={resetForm}
					disabled={submitting}
				>
					Reset
				</button>
				<button type="submit" class="feedback-submit-btn rounded-md px-4 py-2 text-sm font-semibold text-white" disabled={submitting}>
					{submitting ? 'Submitting...' : 'Submit Feedback'}
				</button>
			</div>
		</form>
	</AlertDialog.Content>
</AlertDialog.Root>

<style>
	.feedback-header {
		background-color: #1a337e;
	}

	.feedback-reset-btn {
		background-color: #f3f4f6;
		color: #374151;
	}

	.feedback-reset-btn:hover:not(:disabled) {
		background-color: #e5e7eb;
	}

	.feedback-submit-btn {
		background-color: #1a337e;
	}

	.feedback-submit-btn:hover:not(:disabled) {
		background-color: #152966;
	}

	.feedback-submit-btn:disabled,
	.feedback-reset-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.feedback-attach-btn {
		background-color: #f3f4f6;
		color: #1a337e;
	}

	.feedback-attach-btn:hover {
		background-color: #e5e7eb;
	}
</style>
