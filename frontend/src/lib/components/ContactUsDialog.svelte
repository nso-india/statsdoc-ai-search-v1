<script lang="ts">
    import * as AlertDialog from "$lib/components/ui/alert-dialog";
    import { Button } from "$lib/components/ui/button";
    import Mail from '@lucide/svelte/icons/mail';
    import MapPin from '@lucide/svelte/icons/map-pin';
    import MessageCircle from '@lucide/svelte/icons/message-circle';
    import X from '@lucide/svelte/icons/x';

    let { open = $bindable(false) } = $props();
</script>

<AlertDialog.Root bind:open>
    <AlertDialog.Trigger asChild>
        {#snippet children({ props })}
            <slot {props}></slot>
        {/snippet}
    </AlertDialog.Trigger>
    <AlertDialog.Content 
        class="sm:max-w-[525px]" 
        oninteractoutside={() => open = false}
    >
        <button
            onclick={() => open = false}
            class="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground"
            aria-label="Close"
        >
            <X class="h-4 w-4" />
            <span class="sr-only">Close</span>
        </button>
        <AlertDialog.Header>
            <AlertDialog.Title class="text-2xl">Contact Us</AlertDialog.Title>
            <AlertDialog.Description>
                Get in touch with us for any queries or assistance
            </AlertDialog.Description>
        </AlertDialog.Header>
        
        <div class="space-y-6 py-4">
            <div class="flex items-start gap-4">
                <div class="flex-shrink-0 mt-1">
                    <MapPin class="h-5 w-5 text-blue-600" />
                </div>
                <div class="space-y-1">
                    <h3 class="font-semibold text-base text-gray-900">Address</h3>
                    <div class="text-sm text-gray-700 leading-relaxed">
                        <p>Web Unit, Data Informatics and Innovation Division,</p>
                        <p>Ministry of Statistics and Programme Implementation,</p>
                        <p>East Block – 10, Sector 1, R. K. Puram 110066</p>
                    </div>
                </div>
            </div>

            <div class="flex items-start gap-4">
                <div class="flex-shrink-0 mt-1">
                    <Mail class="h-5 w-5 text-blue-600" />
                </div>
                <div class="space-y-1">
                    <h3 class="font-semibold text-base text-gray-900">Email</h3>
                    <a 
                        href="mailto:di.lab@mospi.gov.in" 
                        class="text-sm text-blue-600 hover:underline"
                    >
                        di.lab@mospi.gov.in
                    </a>
                </div>
            </div>

            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-start gap-3">
                    <MessageCircle class="h-5 w-5 text-blue-700 flex-shrink-0 mt-0.5" />
                    <p class="text-sm text-blue-900">
                        For technical support and assistance with MoSPI StatsDoc AI Assistant, 
                        please reach out to us via email.
                    </p>
                </div>
            </div>
        </div>
    </AlertDialog.Content>
</AlertDialog.Root>

<style>
    .text-sm {
        font-size: 0.875rem;
    }
    .text-base {
        font-size: 1rem;
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
    .text-blue-700 {
        color: #1e40af;
    }
    .text-blue-900 {
        color: #1e3a8a;
    }
</style>
