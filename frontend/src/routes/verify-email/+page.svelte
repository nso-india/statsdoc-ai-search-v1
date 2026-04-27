<script lang="ts">
    import { Button } from "$lib/components/ui/button";
    import * as Card from "$lib/components/ui/card";
    import { Input } from "$lib/components/ui/input";
    import { Label } from "$lib/components/ui/label";
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { toast } from 'svelte-sonner';
    import { Spinner } from "$lib/components/ui/loading";
    import { WEBUI_BASE_URL } from '$lib/constants/app';
    import { onMount } from 'svelte';
    import PublicNavbar from "$lib/components/layout/PublicNavbar.svelte";
import PublicFooter from "$lib/components/PublicFooter.svelte";

    // State
    let loading = $state(false);
    let resendLoading = $state(false);
    let verified = $state(false);
    let errorMessage = $state('');
    let successMessage = $state('');
    let resendEmail = $state('');
    let showResendForm = $state(false);

    // Get email and token from URL parameters
    let email = $derived($page.url.searchParams.get('email') || '');
    let token = $derived($page.url.searchParams.get('token') || '');

    onMount(() => {
        // Auto-verify if email and token are provided in URL
        if (email && token) {
            handleEmailVerification(email, token);
        } else {
            // Show resend form if no verification parameters
            showResendForm = true;
        }
    });

    async function handleEmailVerification(verifyEmail: string, verifyToken: string) {
        try {
            loading = true;
            errorMessage = '';
            successMessage = '';

            const response = await fetch(`${WEBUI_BASE_URL}/api/verify-email/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: verifyEmail,
                    token: verifyToken
                })
            });

            const data = await response.json();

            if (response.ok) {
                verified = true;
                successMessage = data.message || 'Email verified successfully! You can now log in to your account.';
                toast.success('Email verified successfully!');
                
                // Redirect to login after 3 seconds
                setTimeout(() => {
                    goto('/login');
                }, 3000);
            } else {
                if (data.detail) {
                    errorMessage = data.detail;
                } else if (data.non_field_errors) {
                    errorMessage = Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors;
                } else {
                    errorMessage = 'Email verification failed. Please try again or request a new verification email.';
                }
                
                showResendForm = true;
                toast.error(errorMessage);
            }
        } catch (error: any) {
            console.error('Email verification error:', error);
            errorMessage = 'Unable to verify email. Please check your internet connection and try again.';
            showResendForm = true;
            toast.error('Unable to verify email. Please try again.');
        } finally {
            loading = false;
        }
    }

    async function handleResendVerification() {
        if (!resendEmail.trim()) {
            toast.error('Please enter your email address');
            return;
        }

        try {
            resendLoading = true;
            errorMessage = '';
            
            const response = await fetch(`${WEBUI_BASE_URL}/api/resend-verification/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: resendEmail.trim()
                })
            });

            const data = await response.json();

            if (response.ok) {
                successMessage = data.message || 'Verification email sent successfully. Please check your email.';
                toast.success('Verification email sent successfully!');
            } else {
                if (data.detail) {
                    errorMessage = data.detail;
                } else if (data.email) {
                    errorMessage = Array.isArray(data.email) ? data.email[0] : data.email;
                } else {
                    errorMessage = 'Failed to send verification email. Please try again.';
                }
                toast.error(errorMessage);
            }
        } catch (error: any) {
            console.error('Resend verification error:', error);
            errorMessage = 'Unable to send verification email. Please try again.';
            toast.error('Unable to send verification email. Please try again.');
        } finally {
            resendLoading = false;
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter' && !resendLoading) {
            handleResendVerification();
        }
    }
</script>

<svelte:head>
    <title>Verify Email - MOSPI</title>
</svelte:head>

<PublicNavbar />

<div class="min-h-[calc(100vh-140px)] bg-gray-100 p-4 overflow-auto">
    <div class="flex justify-center py-8">
        <div class="w-full max-w-md space-y-6">
        <Card.Root>
            <Card.Header>
                <Card.Title class="text-2xl text-center">
                    {#if verified}
                        ✅ Email Verified!
                    {:else if loading}
                        Verifying Email...
                    {:else}
                        Verify Your Email
                    {/if}
                </Card.Title>
                <Card.Description class="text-center">
                    {#if verified}
                        Your email has been successfully verified. You will be redirected to the login page.
                    {:else if loading}
                        Please wait while we verify your email address.
                    {:else if showResendForm}
                        Enter your email address to receive a new verification link.
                    {:else}
                        Checking your verification link...
                    {/if}
                </Card.Description>
            </Card.Header>
            
            <Card.Content class="grid gap-4">
                {#if loading}
                    <div class="flex justify-center py-8">
                        <Spinner size="lg" />
                    </div>
                {:else if verified}
                    <div class="text-center py-4">
                        <div class="text-6xl mb-4">🎉</div>
                        <p class="text-green-700 font-medium">Welcome to MOSPI!</p>
                        <p class="text-sm text-gray-600 mt-2">Redirecting to login page...</p>
                    </div>
                {:else}
                    {#if successMessage}
                        <div class="p-3 text-sm text-green-700 bg-green-50 border border-green-200 rounded-md">
                            {successMessage}
                        </div>
                    {/if}

                    {#if errorMessage}
                        <div class="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md">
                            {errorMessage}
                        </div>
                    {/if}

                    {#if showResendForm}
                        <div class="grid gap-2">
                            <Label for="email">Email Address</Label>
                            <Input 
                                id="email" 
                                type="email" 
                                placeholder="Enter your email address" 
                                bind:value={resendEmail} 
                                required 
                                disabled={resendLoading}
                                on:keydown={handleKeydown}
                            />
                        </div>
                    {/if}
                {/if}
            </Card.Content>
            
            {#if !verified && !loading}
                <Card.Footer class="flex flex-col gap-4">
                    {#if showResendForm}
                        <Button class="w-full" onclick={handleResendVerification} disabled={resendLoading}>
                            {#if resendLoading}
                                <Spinner size="sm" className="mr-2" />
                            {/if}
                            {resendLoading ? 'Sending...' : 'Send Verification Email'}
                        </Button>
                    {/if}
                    
                    <div class="text-center text-sm text-gray-600">
                        <div>
                            <a href="/login" class="text-blue-600 hover:underline font-medium">
                                Back to Login
                            </a>
                        </div>
                        <div class="mt-2">
                            Don't have an account? 
                            <a href="/signup" class="text-blue-600 hover:underline font-medium">
                                Sign up
                            </a>
                        </div>
                    </div>
                </Card.Footer>
            {:else if verified}
                <Card.Footer>
                    <Button class="w-full" onclick={() => goto('/login')}>
                        Go to Login
                    </Button>
                </Card.Footer>
            {/if}
        </Card.Root>
        
        {#if !verified && !loading}
            <div class="text-center text-sm text-gray-500 space-y-2">
                <p>
                    <strong>Didn't receive the email?</strong>
                </p>
            </div>
        {/if}
        </div>
    </div>
</div>

<PublicFooter />

<style>
    .bg-gray-100 {
        background-color: #f3f4f6;
    }
    .text-green-700 {
        color: #15803d;
    }
    .bg-green-50 {
        background-color: #f0fdf4;
    }
    .bg-red-50 {
        background-color: #fef2f2;
    }
    .border-green-200 {
        border-color: #bbf7d0;
    }
    .border-red-200 {
        border-color: #fecaca;
    }
    .text-sm {
        font-size: 0.875rem;
    }
    .text-gray-600 {
        color: #4b5563;
    }
    .text-gray-500 {
        color: #6b7280;
    }
    .text-blue-600 {
        color: #16306b;
    }
</style>
