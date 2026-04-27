<script lang="ts">
    import PublicNavbar from "$lib/components/layout/PublicNavbar.svelte";
    import * as Card from "$lib/components/ui/card";
    import Mail from '@lucide/svelte/icons/mail';
    import MapPin from '@lucide/svelte/icons/map-pin';
</script>

<svelte:head>
    <title>Contact Us - MoSPI StatsDoc AI Assistant</title>
</svelte:head>

<PublicNavbar />

<div class="min-h-screen bg-gray-100 flex items-center justify-center p-4">
    <div class="w-full max-w-2xl space-y-6">
        <Card.Root>
            <Card.Header>
                <Card.Title class="text-3xl text-center mb-2">Contact Us</Card.Title>
                <Card.Description class="text-center text-base">
                    Get in touch with us for any queries or assistance
                </Card.Description>
            </Card.Header>
            <Card.Content class="space-y-6">
                <div class="flex items-start gap-4">
                    <div class="flex-shrink-0 mt-1">
                        <MapPin class="h-6 w-6 text-blue-600" />
                    </div>
                    <div class="space-y-2">
                        <h3 class="font-semibold text-lg text-gray-900">Address</h3>
                        <div class="text-gray-700 leading-relaxed">
                            <p>Web Unit, Data Informatics and Innovation Division,</p>
                            <p>Ministry of Statistics and Programme Implementation,</p>
                            <p>East Block – 10, Sector 1, R. K. Puram 110066</p>
                        </div>
                    </div>
                </div>

                <div class="flex items-start gap-4">
                    <div class="flex-shrink-0 mt-1">
                        <Mail class="h-6 w-6 text-blue-600" />
                    </div>
                    <div class="space-y-2">
                        <h3 class="font-semibold text-lg text-gray-900">Email</h3>
                        <a 
                            href="mailto:di.lab@mospi.gov.in" 
                            class="text-blue-600 hover:underline text-base"
                        >
                            di.lab@mospi.gov.in
                        </a>
                    </div>
                </div>

                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
                    <p class="text-sm text-blue-900">
                        For technical support and assistance with MoSPI StatsDoc AI Assistant, 
                        please reach out to us via email.
                    </p>
                </div>
            </Card.Content>
            <Card.Footer class="flex flex-col gap-4 pt-6">
                <div class="text-center text-sm text-gray-600">
                    <a href="/login" class="text-blue-600 hover:underline font-medium">
                        Back to Login
                    </a>
                </div>
            </Card.Footer>
        </Card.Root>
    </div>
</div>

<style>
    .bg-gray-100 {
        background-color: #f3f4f6;
    }
    .text-sm {
        font-size: 0.875rem;
    }
    .text-base {
        font-size: 1rem;
    }
    .text-lg {
        font-size: 1.125rem;
    }
    .text-3xl {
        font-size: 1.875rem;
    }
    .text-gray-600 {
        color: #4b5563;
    }
    .text-gray-700 {
        color: #374151;
    }
    .text-gray-900 {
        color: #111827;
    }
    .text-blue-600 {
        color: #16306b;
    }
    .text-blue-900 {
        color: #1e3a8a;
    }
    .bg-blue-50 {
        background-color: #eff6ff;
    }
    .border-blue-200 {
        border-color: #bfdbfe;
    }
</style>
