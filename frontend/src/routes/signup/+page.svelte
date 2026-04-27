<script lang="ts">
    import { Button } from "$lib/components/ui/button";
    import * as Card from "$lib/components/ui/card";
    import { Input } from "$lib/components/ui/input";
    import { Label } from "$lib/components/ui/label";
    import * as RadioGroup from "$lib/components/ui/radio-group";
    import { goto } from '$app/navigation';
    import { toast } from 'svelte-sonner';
    import { Spinner } from "$lib/components/ui/loading";
    import { WEBUI_BASE_URL } from '$lib/constants/app';
    import PublicNavbar from "$lib/components/layout/PublicNavbar.svelte";
    import ContactUsDialog from "$lib/components/ContactUsDialog.svelte";
import PublicFooter from "$lib/components/PublicFooter.svelte";

    // Form state
    let firstName = $state('');
    let lastName = $state('');
    let email = $state('');
    let phone = $state('');
    let userType = $state('individual');
    let organizationName = $state('');
    let password = $state('');
    let loading = $state(false);
    let errorMessage = $state('');
    let successMessage = $state('');
    let contactUsOpen = $state(false);

    // Validation states
    let emailError = $state('');
    let passwordError = $state('');
    let organizationError = $state('');
    let showResendOption = $state(false);
    function validateEmail(email: string): boolean {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
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

    function validateForm(): boolean {
        let isValid = true;
        
        // Reset errors
        emailError = '';
        passwordError = '';
        organizationError = '';
        errorMessage = '';

        // Email validation
        if (!email.trim()) {
            emailError = 'Email is required';
            isValid = false;
        } else if (!validateEmail(email)) {
            emailError = 'Please enter a valid email address';
            isValid = false;
        }

        // Password validation
        if (!password) {
            passwordError = 'Password is required';
            isValid = false;
        } else {
            const passwordValidationErrors = validatePassword(password);
            if (passwordValidationErrors.length > 0) {
                passwordError = passwordValidationErrors[0]; // Show first error
                isValid = false;
            }
        }

        // Organization name validation for company type
        if (userType === 'company' && !organizationName.trim()) {
            organizationError = 'Organization name is required for company accounts';
            isValid = false;
        }

        return isValid;
    }

    async function handleSignup() {
        if (!validateForm()) {
            return;
        }

        try {
            loading = true;
            errorMessage = '';
            successMessage = '';

            const signupData = {
                first_name: firstName.trim(),
                last_name: lastName.trim(),
                email: email.trim(),
                phone: phone.trim(),
                user_type: userType,
                organization_name: userType === 'company' ? organizationName.trim() : '',
                password: password
            };

            const response = await fetch(`${WEBUI_BASE_URL}/api/signup/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                credentials: 'omit', // Try without credentials first
                body: JSON.stringify(signupData)
            });

            const data = await response.json();


            if (response.ok) {
                successMessage = data.message || 'Account created successfully! Please check your email to verify your account.';
                toast.success('Account created successfully! Please check your email for verification.');
                
                // Redirect to login after 3 seconds
                setTimeout(() => {
                    goto('/login');
                }, 3000);
            } else {
                // Handle validation errors
                if (data.email) {
                    const emailErr = Array.isArray(data.email) ? data.email[0] : data.email;
                    emailError = emailErr;
                    
                    // Show specific toast messages based on error type
                    if (emailErr.includes('already exists and is active')) {
                        toast.error('Account already exists! Try logging in instead.', {
                            action: {
                                label: 'Login',
                                onClick: () => goto('/login')
                            }
                        });
                    } else if (emailErr.includes("hasn't been verified")) {
                        showResendOption = true;
                        toast.error('Account exists but not verified. Check your email!', {
                            action: {
                                label: 'Resend Email',
                                onClick: () => goto('/verify-email')
                            }
                        });
                    }
                }
                if (data.password) {
                    passwordError = Array.isArray(data.password) ? data.password[0] : data.password;
                }
                if (data.organization_name) {
                    organizationError = Array.isArray(data.organization_name) ? data.organization_name[0] : data.organization_name;
                }
                
                // General error message
                if (data.detail) {
                    errorMessage = data.detail;
                } else if (data.non_field_errors) {
                    errorMessage = Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors;
                } else {
                    errorMessage = 'Please correct the errors above and try again.';
                }

                toast.error(errorMessage || 'Please correct the errors and try again.');
            }
        } catch (error: any) {
            console.error('Signup error:', error);
            errorMessage = 'Unable to create account. Please check your internet connection and try again.';
            toast.error('Unable to create account. Please try again.');
        } finally {
            loading = false;
        }
    }

    async function handleResendVerification() {
        try {
            loading = true;
            errorMessage = '';
            
            const emailToSend = email.trim();
            
            if (!emailToSend) {
                toast.error('Please enter a valid email address first.');
                return;
            }
            
            const response = await fetch(`${WEBUI_BASE_URL}/api/resend-verification/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                credentials: 'omit',
                body: JSON.stringify({
                    email: emailToSend
                })
            });

            const data = await response.json();

            if (response.ok) {
                successMessage = 'Verification email sent! Please check your inbox.';
                toast.success('Verification email sent! Please check your inbox.');
                showResendOption = false;
            } else {
                const errorMsg = data.error || data.detail || 'Failed to send verification email.';
                toast.error(errorMsg);
            }
        } catch (error: any) {
            console.error('Resend verification error:', error);
            toast.error('Failed to send verification email. Please try again.');
        } finally {
            loading = false;
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter' && !loading) {
            handleSignup();
        }
    }

    // Watch for user type changes to clear organization data when switching to individual
    $effect(() => {
        if (userType === 'individual') {
            organizationError = '';
            organizationName = '';
        }
    });
</script>

<svelte:head>
    <title>Sign Up - MOSPI</title>
</svelte:head>

<PublicNavbar />

<div class="bg-gray-100 p-4 overflow-auto min-h-0 w-full" style="padding-top: var(--public-header-height, 120px); padding-bottom: 1.25rem;">
    <div class="flex justify-center items-start py-8">
        <div class="center-viewport w-full">
            <div class="w-full max-w-md space-y-6">
        <Card.Root class="w-full shadow-lg border-0">
            <Card.Header class="space-y-1 pb-6">
                <Card.Title class="text-2xl font-semibold text-center text-gray-900">Create Account</Card.Title>
                <Card.Description class="text-center text-gray-600">
                    Enter your information below to create your account
                </Card.Description>
            </Card.Header>
            
            <Card.Content class="grid gap-4">
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

                <!-- Name fields -->
                <div class="grid grid-cols-2 gap-4">
                    <div class="grid gap-2">
                        <Label for="firstName">First Name</Label>
                        <Input 
                            id="firstName" 
                            type="text" 
                            placeholder="John" 
                            bind:value={firstName} 
                            disabled={loading}
                            oncopy={(e) => e.preventDefault()}
                            onpaste={(e) => e.preventDefault()}
                            oncut={(e) => e.preventDefault()}
                        />
                    </div>
                    <div class="grid gap-2">
                        <Label for="lastName">Last Name</Label>
                        <Input 
                            id="lastName" 
                            type="text" 
                            placeholder="Doe" 
                            bind:value={lastName} 
                            disabled={loading}
                            oncopy={(e) => e.preventDefault()}
                            onpaste={(e) => e.preventDefault()}
                            oncut={(e) => e.preventDefault()}
                        />
                    </div>
                </div>

                <!-- Email -->
                <div class="grid gap-2">
                    <Label for="email">Email <span class="text-red-500">*</span></Label>
                    <Input 
                        id="email" 
                        type="email" 
                        placeholder="john@example.com" 
                        bind:value={email} 
                        required 
                        disabled={loading}
                        oncopy={(e) => e.preventDefault()}
                        onpaste={(e) => e.preventDefault()}
                        oncut={(e) => e.preventDefault()}
                    />
                    {#if emailError}
                        <span class="text-sm text-red-500">{emailError}</span>
                        {#if showResendOption}
                            <div class="mt-2">
                                <Button 
                                    type="button" 
                                    variant="outline" 
                                    size="sm" 
                                    onclick={handleResendVerification}
                                    disabled={loading}
                                >
                                    Resend Verification Email
                                </Button>
                            </div>
                        {/if}
                    {/if}
                </div>

                <!-- Phone -->
                <div class="grid gap-2">
                    <Label for="phone">Phone Number</Label>
                    <Input 
                        id="phone" 
                        type="tel" 
                        placeholder="+1 (555) 123-4567" 
                        bind:value={phone} 
                        disabled={loading}
                        oncopy={(e) => e.preventDefault()}
                        onpaste={(e) => e.preventDefault()}
                        oncut={(e) => e.preventDefault()}
                    />
                </div>

                <!-- User Type -->
                <div class="grid gap-3">
                    <Label>Account Type <span class="text-red-500">*</span></Label>
                    <RadioGroup.Root bind:value={userType} class="flex flex-row space-x-6">
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

                <!-- Organization Name (only for company type) -->
                {#if userType === 'company'}
                    <div class="grid gap-2">
                        <Label for="organizationName">Organization Name <span class="text-red-500">*</span></Label>
                        <Input 
                            id="organizationName" 
                            type="text" 
                            placeholder="Your Company Name" 
                            bind:value={organizationName} 
                            required 
                            disabled={loading}
                            oncopy={(e) => e.preventDefault()}
                            onpaste={(e) => e.preventDefault()}
                            oncut={(e) => e.preventDefault()}
                        />
                        {#if organizationError}
                            <span class="text-sm text-red-500">{organizationError}</span>
                        {/if}
                    </div>
                {/if}

                <!-- Password -->
                <div class="grid gap-2">
                    <Label for="password">Password <span class="text-red-500">*</span></Label>
                    <Input 
                        id="password" 
                        type="password" 
                        bind:value={password} 
                        required 
                        disabled={loading}
                        oncopy={(e) => e.preventDefault()}
                        onpaste={(e) => e.preventDefault()}
                        oncut={(e) => e.preventDefault()}
                    />
                    {#if passwordError}
                        <span class="text-sm text-red-500">{passwordError}</span>
                    {/if}
                </div>

                <div class="text-xs text-gray-600">
                    Password must be at least 8 characters with uppercase, lowercase, and numbers.
                </div>
            </Card.Content>
            
            <Card.Footer class="flex flex-col gap-4">
                <Button class="w-full" onclick={handleSignup} disabled={loading}>
                    {#if loading}
                        <Spinner size="sm" className="mr-2" />
                    {/if}
                    {loading ? 'Creating Account...' : 'Create Account'}
                </Button>
                
                <div class="text-center text-sm text-gray-600">
                    Already have an account? 
                    <a href="/login" class="text-blue-600 hover:underline font-medium">
                        Sign in
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
</div>

<PublicFooter />

<style>
    .bg-gray-100 {
        background-color: #f3f4f6;
    }
    .text-red-500 {
        color: #ef4444;
    }
    .text-green-700 {
        color: #15803d;
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
    .text-xs {
        font-size: 0.75rem;
    }
    .text-gray-600 {
        color: #4b5563;
    }
    .text-blue-600 {
        color: #16306b;
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
