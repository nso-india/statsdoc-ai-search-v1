<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Modal from '$lib/components/common/Modal.svelte';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import * as RadioGroup from '$lib/components/ui/radio-group';
	import { Spinner } from '$lib/components/ui/loading';
	import { UsersAPI } from '$lib/api/users';
	import X from 'lucide-svelte/icons/x';

	const dispatch = createEventDispatcher();

	export let show = false;

	let loading = false;
	let userForm = {
		username: '',
		email: '',
		password: '',
		first_name: '',
		last_name: '',
		phone: '',
		user_type: 'individual' as 'individual' | 'company',
		organization_name: '',
		is_active: true
	};

	$: if (show) {
		userForm = {
			username: '',
			email: '',
			password: '',
			first_name: '',
			last_name: '',
			phone: '',
			user_type: 'individual' as 'individual' | 'company',
			organization_name: '',
			is_active: true
		};
	}

	const submitHandler = async () => {
		if (!userForm.email || !userForm.password) {
			toast.error('Please fill in all required fields');
			return;
		}

		if (userForm.user_type === 'company' && !userForm.organization_name) {
			toast.error('Organization name is required for company accounts');
			return;
		}

		loading = true;
		try {
			const userData: any = {
				email: userForm.email,
				password: userForm.password,
				first_name: userForm.first_name,
				last_name: userForm.last_name,
				phone: userForm.phone,
				user_type: userForm.user_type,
				is_active: userForm.is_active
			};

			// Only include organization_name if it's not empty
			if (userForm.organization_name) {
				userData.organization_name = userForm.organization_name;
			}

			// Only include username if it's not empty, otherwise backend will use email
			if (userForm.username) {
				userData.username = userForm.username;
			}

			const response = await UsersAPI.createUser(userData);
			
			dispatch('save', {
				user: response
			});
			
			show = false;
			toast.success('User created successfully');
		} catch (error) {
			console.error('Error creating user:', error);
			toast.error(error instanceof Error ? error.message : 'Failed to create user');
		} finally {
			loading = false;
		}
	};
</script>

<Modal size="sm" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
			<div class="text-lg font-medium self-center">Add User</div>
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
			<form
				class="flex flex-col w-full"
				on:submit|preventDefault={() => {
					submitHandler();
				}}
			>
				<div class="px-1">
					<div class="flex flex-col w-full mb-3">
						<Label class="mb-1 text-xs text-gray-500">Status</Label>
						<select
							bind:value={userForm.is_active}
							class="w-full text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value={true}>Active</option>
							<option value={false}>Inactive</option>
						</select>
					</div>

					<div class="flex flex-col w-full mb-3">
						<Label class="mb-1 text-xs text-gray-500">Account Type *</Label>
						<RadioGroup.Root bind:value={userForm.user_type} class="flex flex-row gap-4 mt-2">
							<div class="flex items-center space-x-2">
								<RadioGroup.Item value="individual" id="individual" />
								<Label for="individual" class="text-sm font-normal cursor-pointer">Individual</Label>
							</div>
							<div class="flex items-center space-x-2">
								<RadioGroup.Item value="company" id="company" />
								<Label for="company" class="text-sm font-normal cursor-pointer">Company</Label>
							</div>
						</RadioGroup.Root>
					</div>

					{#if userForm.user_type === 'company'}
					<div class="flex flex-col w-full mb-3">
						<Label class="mb-1 text-xs text-gray-500">Organization Name *</Label>
						<Input
							type="text"
							bind:value={userForm.organization_name}
							placeholder="Enter organization name"
							required
							class="w-full text-sm bg-transparent"
						/>
					</div>
					{/if}

					<div class="flex flex-col w-full mt-1">
						<Label class="mb-1 text-xs text-gray-500">Username</Label>
						<Input
							type="text"
							bind:value={userForm.username}
							placeholder="Enter username (optional)"
							class="w-full text-sm bg-transparent"
						/>
					</div>

					<hr class="border-gray-100 dark:border-gray-850 my-2.5 w-full" />

					<div class="flex flex-col w-full">
						<Label class="mb-1 text-xs text-gray-500">Email *</Label>
						<Input
							type="email"
							bind:value={userForm.email}
							placeholder="Enter email address"
							required
							class="w-full text-sm bg-transparent"
						/>
					</div>

					<div class="flex flex-col w-full mt-1">
						<Label class="mb-1 text-xs text-gray-500">First Name</Label>
						<Input
							type="text"
							bind:value={userForm.first_name}
							placeholder="Enter first name (optional)"
							class="w-full text-sm bg-transparent"
						/>
					</div>

					<div class="flex flex-col w-full mt-1">
						<Label class="mb-1 text-xs text-gray-500">Last Name</Label>
						<Input
							type="text"
							bind:value={userForm.last_name}
							placeholder="Enter last name (optional)"
							class="w-full text-sm bg-transparent"
						/>
					</div>

					<div class="flex flex-col w-full mt-1">
						<Label class="mb-1 text-xs text-gray-500">Phone</Label>
						<Input
							type="tel"
							bind:value={userForm.phone}
							placeholder="Enter phone number (optional)"
							class="w-full text-sm bg-transparent"
						/>
					</div>

					<div class="flex flex-col w-full mt-1">
						<Label class="mb-1 text-xs text-gray-500">Password *</Label>
						<Input
							type="password"
							bind:value={userForm.password}
							placeholder="Enter password"
							required
							class="w-full text-sm bg-transparent"
						/>
					</div>
				</div>

				<div class="flex justify-end pt-3 text-sm font-medium">
					<Button
						type="submit"
						disabled={loading}
						class="px-3.5 py-1.5 text-sm font-medium bg-primary hover:bg-primary/90 text-white transition rounded-full flex flex-row space-x-1 items-center disabled:cursor-not-allowed"
					>
						Save
						{#if loading}
							<div class="ml-2 self-center">
								<Spinner />
							</div>
						{/if}
					</Button>
				</div>
			</form>
		</div>
	</div>
</Modal>
