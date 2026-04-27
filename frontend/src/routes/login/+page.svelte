<script lang="ts">
    import { Button } from "$lib/components/ui/button";
    import * as Card from "$lib/components/ui/card";
    import { Input } from "$lib/components/ui/input";
    import { Label } from "$lib/components/ui/label";
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { user, authToken, isAuthenticated, loginUser } from '$lib/stores';
    import { toast } from 'svelte-sonner';
    import { get } from 'svelte/store';
    import { onMount } from 'svelte';
    import { Spinner } from "$lib/components/ui/loading";
    import PublicNavbar from "$lib/components/layout/PublicNavbar.svelte";
    import ContactUsDialog from "$lib/components/ContactUsDialog.svelte";
    import PublicFooter from "$lib/components/PublicFooter.svelte";
    import Eye from '@lucide/svelte/icons/eye';
    import EyeOff from '@lucide/svelte/icons/eye-off';

    let username = $state('');
    let password = $state('');
    let errorMessage = $state('');
    let loading = $state(false);
    let showPassword = $state(false);
    let contactUsOpen = $state(false);

    // Get redirect parameter from URL
    const redirectUrl = $derived($page.url.searchParams.get('redirect'));



    // Function to determine post-login redirect based on user role
    function getPostLoginRedirect(userData: any): string {
        if (redirectUrl) {
            return redirectUrl; // Honor explicit redirect if provided
        }
        
        // Default redirect to /c for all users
        return '/c';
    }

    async function handleLogin() {
        try {
            loading = true;
            errorMessage = '';

            // Basic validation
            if (!username.trim()) {
                throw new Error('Username is required');
            }
            if (!password.trim()) {
                throw new Error('Password is required');
            }

            await loginUser(username, password);
            toast.success('Successfully logged in!');
            
            // Get current user data and redirect to appropriate page
            const currentUser = get(user);
            const postLoginRedirect = getPostLoginRedirect(currentUser);
            goto(postLoginRedirect);
        } catch (error: any) {
            console.error('Login error:', error);
            
            // Handle different types of errors
            let displayMessage = 'An unexpected error occurred';

            if (error && typeof error === 'object') {
                // Handle Django REST Framework error responses
                if (error.detail) {
                    if (typeof error.detail === 'string') {
                        displayMessage = error.detail;
                    } else if (Array.isArray(error.detail)) {
                        displayMessage = error.detail.join(' ');
                    } else if (typeof error.detail === 'object') {
                        // Flatten object values (arrays or strings) into a single message
                        const parts: string[] = [];
                        for (const key of Object.keys(error.detail)) {
                            const val = (error.detail as any)[key];
                            if (Array.isArray(val)) parts.push(val.join(' '));
                            else if (typeof val === 'string') parts.push(val);
                            else parts.push(JSON.stringify(val));
                        }
                        displayMessage = parts.join(' ');
                    }
                }
                // Handle non_field_errors or similar structures
                else if (error.non_field_errors) {
                    displayMessage = Array.isArray(error.non_field_errors) ? error.non_field_errors.join(' ') : String(error.non_field_errors);
                }
                // Handle validation errors on specific fields
                else if (error.username) {
                    displayMessage = Array.isArray(error.username) ? `Username: ${error.username.join(', ')}` : `Username: ${error.username}`;
                }
                else if (error.password) {
                    displayMessage = Array.isArray(error.password) ? `Password: ${error.password.join(', ')}` : `Password: ${error.password}`;
                }
                // Handle generic error messages
                else if (error.message) {
                    displayMessage = error.message;
                }
                // Handle network errors
                else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                    displayMessage = 'Unable to connect to server. Please check your internet connection.';
                }
                // Handle timeout errors
                else if (error.name === 'AbortError') {
                    displayMessage = 'Request timed out. Please try again.';
                }
            }
            // Handle string errors
            else if (typeof error === 'string') {
                displayMessage = error;
            }

            // Map some backend messages to user-friendly ones, but prefer the backend message when it contains extra info
            const msgLower = String(displayMessage).toLowerCase();

            if ((msgLower.includes('invalid credentials') || msgLower.includes('unable to log in') || msgLower.includes('no active account found')) && !msgLower.includes('attempt')) {
                // Only replace with a generic message if no extra detail (like attempts remaining) is present
                displayMessage = 'Invalid email/username or password. Please try again.';
            }
            else if (msgLower.includes('user is not active') || msgLower.includes('account is not active')) {
                displayMessage = 'Your account is not active. Please check your email for a verification link.';
                // Show a link to resend verification
                errorMessage = displayMessage + ' Need to resend verification? ';
                toast.error(displayMessage);
                return; // Don't set errorMessage again below
            }
            else if (msgLower.includes('too many')) {
                displayMessage = 'Too many login attempts. Please try again later.';
            }

            errorMessage = displayMessage;
            toast.error(displayMessage);
        } finally {
            loading = false;
        }
    }

    onMount(() => {
        // Check if user is already authenticated
        const currentUser = get(user);
        if (get(isAuthenticated) && currentUser) {
            const postLoginRedirect = getPostLoginRedirect(currentUser);
            goto(postLoginRedirect);
        }
    });

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter' && !loading) {
            handleLogin();
        }
    }
</script>

<svelte:head>
    <title>Login - MOSPI</title>
</svelte:head>

<PublicNavbar />

<div class="bg-gray-100 flex md:items-center items-start justify-center px-4 overflow-auto min-h-0 w-full" style="padding-top: var(--public-header-height, 120px); padding-bottom: 1.25rem;">
    <div class="center-viewport w-full">
      <div class="w-full max-w-sm space-y-6 mt-6 md:mt-0">
        
        <Card.Root>
            <Card.Header>
                <Card.Title class="text-2xl text-center">Login</Card.Title>
                <Card.Description class="text-center">Enter your email and password below to login to your account.</Card.Description>
            </Card.Header>
            <Card.Content class="grid gap-4">
                {#if errorMessage}
                    <div class="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md">
                        {errorMessage}
                    </div>
                {/if}
            <div class="grid gap-2">
                <Label for="username">Email or Username</Label>
                <Input 
                    id="username" 
                    type="text" 
                    placeholder="your_email@example.com" 
                    bind:value={username} 
                    required 
                    disabled={loading}
                    autocomplete="off"
                    oncopy={(e) => e.preventDefault()}
                    onpaste={(e) => e.preventDefault()}
                    oncut={(e) => e.preventDefault()}
                />
            </div>
            <div class="grid gap-2">
                <Label for="password">Password</Label>
                <div class="relative">
                    <Input 
                        id="password" 
                        type={showPassword ? "text" : "password"}
                        bind:value={password} 
                        required 
                        disabled={loading}
                        on:keydown={handleKeydown}
                        oncopy={(e) => e.preventDefault()}
                        onpaste={(e) => e.preventDefault()}
                        oncut={(e) => e.preventDefault()}
                        autocomplete="off"
                        class="pr-10"
                    />
                    <button
                        type="button"
                        class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                        onclick={() => showPassword = !showPassword}
                        tabindex="-1"
                    >
                        {#if showPassword}
                            <Eye class="h-5 w-5" />
                        {:else}
                            <EyeOff class="h-5 w-5" />
                        {/if}
                    </button>
                </div>
            </div>
        </Card.Content>
        <Card.Footer class="flex flex-col gap-4">
            <Button class="w-full" onclick={handleLogin} disabled={loading}>
                {#if loading}
                    <Spinner size="sm" className="mr-2" />
                {/if}
                {loading ? 'Signing in...' : 'Sign in'}
            </Button>
            
            <div class="text-center text-sm text-gray-600">
                <a href="/forgot-password" class="text-blue-600 hover:underline font-medium">
                    Forgot Password?
                </a>
            </div>
            
            <div class="text-center text-sm text-gray-600">
                Don't have an account? 
                <a href="/signup" class="text-blue-600 hover:underline font-medium">
                    Sign up
                </a>
            </div>
            
            <div class="text-center text-sm text-gray-600">
                Need to verify your email? 
                <a href="/verify-email" class="text-blue-600 hover:underline font-medium">
                    Verify email
                </a>
            </div>
            
            <div class="text-center text-sm text-gray-600 pt-2 border-t border-gray-200">
                <ContactUsDialog bind:open={contactUsOpen}>
                    {#snippet children({ props })}
                        <button 
                            {...props}
                            class="text-blue-600 hover:underline font-medium"
                        >
                            Contact Us
                        </button>
                    {/snippet}
                </ContactUsDialog>
            </div>
        </Card.Footer>
        </Card.Root>
    </div>
</div>
</div>

<PublicFooter />

<style>
    .bg-gray-100 {
        background-color: #f3f4f6;
    }
    .text-sm {
        font-size: 0.875rem;
    }
    .text-gray-600 {
        color: #4b5563;
    }
    .text-blue-600 {
        color: #16306b;
    }
    .text-red-700 {
        color: #b91c1c;
    }
    .bg-red-50 {
        background-color: #fef2f2;
    }
    .border-red-200 {
        border-color: #fecaca;
    }

@media (min-width: 768px) {
  .center-viewport {
    min-height: calc(100vh - var(--public-header-height, 120px) - var(--public-footer-height, 72px));
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>