<script lang="ts">
    import { Button } from "$lib/components/ui/button";
    import * as Card from "$lib/components/ui/card";
    import { Input } from "$lib/components/ui/input";
    import { Label } from "$lib/components/ui/label";
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { toast } from 'svelte-sonner';
    import { Spinner } from "$lib/components/ui/loading";
    import PublicNavbar from "$lib/components/layout/PublicNavbar.svelte";
    import { resetPassword } from '$lib/apis/auths';
    import { onMount } from 'svelte';

    let email = $state('');
    let token = $state('');
    let newPassword = $state('');
    let confirmPassword = $state('');
    let errorMessage = $state('');
    let successMessage = $state('');
    let loading = $state(false);

    // Get email and token from URL parameters
    onMount(() => {
        const urlParams = $page.url.searchParams;
        email = urlParams.get('email') || '';
        token = urlParams.get('token') || '';
        
        if (!email || !token) {
            errorMessage = 'Invalid reset link. Please request a new password reset.';
        }
    });

    function handleKeydown(event: CustomEvent<KeyboardEvent>) {
        const e = event.detail;
        if (e.key === 'Enter') {
            handlePasswordReset();
        }
    }

    function validatePassword(password: string): string[] {
        const errors = [];
        if (password.length < 8) {
            errors.push('Password must be at least 8 characters long');
        }
        if (!/(?=.*[a-z])/.test(password)) {
            errors.push('Password must contain at least one lowercase letter');
        }
        if (!/(?=.*[A-Z])/.test(password)) {
            errors.push('Password must contain at least one uppercase letter');
        }
        if (!/(?=.*\d)/.test(password)) {
            errors.push('Password must contain at least one number');
        }
        return errors;
    }

    async function handlePasswordReset() {
        try {
            loading = true;
            errorMessage = '';
            successMessage = '';

            // Basic validation
            if (!newPassword.trim()) {
                throw new Error('New password is required');
            }
            if (!confirmPassword.trim()) {
                throw new Error('Please confirm your password');
            }
            if (newPassword !== confirmPassword) {
                throw new Error('Passwords do not match');
            }

            // Password strength validation
            const passwordErrors = validatePassword(newPassword);
            if (passwordErrors.length > 0) {
                throw new Error(passwordErrors.join('. '));
            }

            if (!email || !token) {
                throw new Error('Invalid reset link. Please request a new password reset.');
            }

            // Call the reset password API
            const response = await resetPassword(email, token, newPassword);
            
            if (response) {
                successMessage = response.message || 'Password reset successfully!';
                toast.success('Password reset successfully! You can now log in with your new password.');
                
                // Redirect to login after success
                setTimeout(() => {
                    goto('/login');
                }, 2000);
            }
            
        } catch (error: any) {
            console.error('Password reset error:', error);
            
            // Handle API errors with better user experience
            let displayMessage = 'An unexpected error occurred';
            
            if (error && typeof error === 'object') {
                // Prefer 'detail' when provided; normalize arrays/objects to string
                if (error.detail) {
                    if (Array.isArray(error.detail)) {
                        displayMessage = error.detail.join(' ');
                    } else if (typeof error.detail === 'object') {
                        // Flatten object values
                        const parts = [];
                        for (const k of Object.keys(error.detail)) {
                            const v = error.detail[k];
                            if (Array.isArray(v)) parts.push(v.join(' '));
                            else if (typeof v === 'string') parts.push(v);
                            else parts.push(String(v));
                        }
                        displayMessage = parts.join(' ');
                    } else {
                        displayMessage = String(error.detail);
                    }
                }
                // Handle validation errors for fields
                else if (error.new_password) {
                    displayMessage = Array.isArray(error.new_password)
                        ? `Password: ${error.new_password.join(', ')}`
                        : `Password: ${error.new_password}`;
                }
                else if (error.email) {
                    displayMessage = Array.isArray(error.email)
                        ? `Email: ${error.email.join(', ')}`
                        : `Email: ${error.email}`;
                }
                else if (error.token) {
                    displayMessage = Array.isArray(error.token)
                        ? `Token: ${error.token.join(', ')}`
                        : `Token: ${error.token}`;
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
                    displayMessage = String(error.message);
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
    <title>Reset Password - MOSPI</title>
</svelte:head>

<div class="h-screen flex flex-col">
    <PublicNavbar />
    
    <div class="flex-1 bg-gray-100 flex items-center justify-center p-4 overflow-auto">
        <div class="w-full max-w-sm space-y-6">
        
        <Card.Root>
            <Card.Header>
                <Card.Title class="text-2xl text-center">Reset Password</Card.Title>
                <Card.Description class="text-center">
                    Enter your new password below.
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
                    <Label for="new-password">New Password</Label>
                    <Input 
                        id="new-password" 
                        type="password" 
                        placeholder="Enter new password"
                        bind:value={newPassword} 
                        required 
                        disabled={loading}
                        oncopy={(e) => e.preventDefault()}
                        onpaste={(e) => e.preventDefault()}
                        oncut={(e) => e.preventDefault()}
                    />
                    <div class="text-xs text-gray-500">
                        Password must be at least 8 characters with uppercase, lowercase, and number.
                    </div>
                </div>
                <div class="grid gap-2">
                    <Label for="confirm-password">Confirm Password</Label>
                    <Input 
                        id="confirm-password" 
                        type="password" 
                        placeholder="Confirm new password"
                        bind:value={confirmPassword} 
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
                <Button class="w-full" onclick={handlePasswordReset} disabled={loading || !email || !token}>
                    {#if loading}
                        <Spinner size="sm" className="mr-2" />
                    {/if}
                    {loading ? 'Resetting...' : 'Reset Password'}
                </Button>
                
                <div class="text-center text-sm text-gray-600">
                    Remember your password? 
                    <a href="/login" class="text-blue-600 hover:underline font-medium">
                        Sign in
                    </a>
                </div>
                
                <div class="text-center text-sm text-gray-600">
                    Need a new reset link? 
                    <a href="/forgot-password" class="text-blue-600 hover:underline font-medium">
                        Request new link
                    </a>
                </div>
            </Card.Footer>
        </Card.Root>
    </div>
</div>
</div>

<style>
    .bg-gray-100 {
        background-color: #f3f4f6;
    }
    .text-sm {
        font-size: 0.875rem;
    }
    .text-xs {
        font-size: 0.75rem;
    }
    .text-gray-500 {
        color: #6b7280;
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

