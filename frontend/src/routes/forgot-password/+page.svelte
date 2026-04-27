<script lang="ts">
    import { Button } from "$lib/components/ui/button";
    import * as Card from "$lib/components/ui/card";
    import { Input } from "$lib/components/ui/input";
    import { Label } from "$lib/components/ui/label";
    import { goto } from '$app/navigation';
    import { toast } from 'svelte-sonner';
    import { Spinner } from "$lib/components/ui/loading";
    import PublicNavbar from "$lib/components/layout/PublicNavbar.svelte";
import PublicFooter from "$lib/components/PublicFooter.svelte";
    import { forgotPassword } from '$lib/apis/auths';

    let email = $state('');
    let errorMessage = $state('');
    let successMessage = $state('');
    let loading = $state(false);

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === 'Enter') {
            handleEmailSubmit();
        }
    }

    async function handleEmailSubmit() {
        try {
            loading = true;
            errorMessage = '';
            successMessage = '';

            // Basic validation
            if (!email.trim()) {
                throw new Error('Email is required');
            }

            // Email format validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                throw new Error('Please enter a valid email address');
            }

            // Call the forgot password API
            const response = await forgotPassword(email);
            
            if (response) {
                successMessage = response.message || 'Password reset email sent successfully. Please check your email.';
                toast.success('Password reset email sent! Check your inbox.');
                
                // Optionally redirect after a few seconds
                setTimeout(() => {
                    goto('/login');
                }, 3000);
            }
            
        } catch (error: any) {
            console.error('Forgot password error:', error);
            
            // Handle API errors with better user experience
            let displayMessage = 'An unexpected error occurred';
            
            if (error && typeof error === 'object') {
                // Handle detailed error responses
                if (error.detail) {
                    displayMessage = error.detail;
                }
                // Handle validation errors for email field
                else if (error.email) {
                    displayMessage = Array.isArray(error.email) 
                        ? `Email: ${error.email.join(', ')}`
                        : `Email: ${error.email}`;
                }
                // Handle network errors
                else if (error.type === 'network_error') {
                    displayMessage = 'Unable to connect to server. Please check your internet connection.';
                }
                // Handle timeout errors
                else if (error.type === 'timeout_error') {
                    displayMessage = 'Request timed out. Please try again.';
                }
                // Handle generic error messages
                else if (error.message) {
                    displayMessage = error.message;
                }
            }
            // Handle string errors
            else if (typeof error === 'string') {
                displayMessage = error;
            }

            errorMessage = displayMessage;
            toast.error(displayMessage);
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>Forgot Password - MOSPI</title>
</svelte:head>

<div class="h-screen flex flex-col">
    <PublicNavbar />
    
    <div class="flex-1 bg-gray-100 flex items-center justify-center p-4 overflow-auto">
        <div class="w-full max-w-sm space-y-6">
        
        <Card.Root>
            <Card.Header>
                <Card.Title class="text-2xl text-center">Forgot Password</Card.Title>
                <Card.Description class="text-center">
                    Enter your email address and we'll send you instructions to reset your password.
                </Card.Description>
            </Card.Header>
            <Card.Content class="grid gap-4">
                {#if errorMessage}
                    <div class="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md">
                        {errorMessage}
                    </div>
                {/if}

                {#if successMessage}
                    <div class="p-3 text-sm text-green-700 bg-green-50 border border-green-200 rounded-md">
                        {successMessage}
                    </div>
                {/if}

                <div class="grid gap-2">
                    <Label for="email">Email Address</Label>
                    <Input 
                        id="email" 
                        type="email" 
                        placeholder="your_email@example.com" 
                        bind:value={email} 
                        required 
                        disabled={loading}
                        on:keydown={handleKeydown}
                        oncopy={(e) => e.preventDefault()}
                        onpaste={(e) => e.preventDefault()}
                        oncut={(e) => e.preventDefault()}
                    />
                </div>
            </Card.Content>
            <Card.Footer class="flex flex-col gap-4">
                <Button class="w-full" onclick={handleEmailSubmit} disabled={loading}>
                    {#if loading}
                        <Spinner size="sm" className="mr-2" />
                    {/if}
                    {loading ? 'Sending...' : 'Send Reset Instructions'}
                </Button>
                
                <div class="text-center text-sm text-gray-600">
                    Remember your password? 
                    <a href="/login" class="text-blue-600 hover:underline font-medium">
                        Sign in
                    </a>
                </div>
                
                <div class="text-center text-sm text-gray-600">
                    Don't have an account? 
                    <a href="/signup" class="text-blue-600 hover:underline font-medium">
                        Sign up
                    </a>
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
    .text-green-700 {
        color: #15803d;
    }
    .bg-green-50 {
        background-color: #f0fdf4;
    }
    .border-green-200 {
        border-color: #bbf7d0;
    }
</style>

