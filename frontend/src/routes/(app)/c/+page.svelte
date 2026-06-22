<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
    import { browser } from '$app/environment';
    import { writable, get } from 'svelte/store';
    import { newChatApi } from '$lib/api/newchat.ts';
    import { WEBSOCKET_BASE_URL, WEBUI_API_BASE_URL } from '$lib/constants.js';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { authToken, user } from '$lib/stores';
    import { fileSizeLimitBytes, initializeSettings } from '$lib/stores/settings';
    import { validateFiles, showFileValidationErrors, getCurrentFileSizeLimit } from '$lib/utils/fileValidation';
    import { validateFileType } from '$lib/apis/files';
    import { toast } from 'svelte-sonner';
    import ArrowUp from '@lucide/svelte/icons/arrow-up';
    import Mic from '@lucide/svelte/icons/mic';
    import Plus from '@lucide/svelte/icons/plus';
    import Paperclip from '@lucide/svelte/icons/paperclip';
    import VoiceRecording from '$lib/components/VoiceRecording.svelte';
    import MarkdownRenderer from '$lib/components/rag/MarkdownRenderer.svelte';
    import PlotlyChart from '$lib/components/charts/PlotlyChart.svelte';
    import FileChip from '$lib/components/ui/FileChip.svelte';
    import * as Tooltip from '$lib/components/ui/tooltip/index.js';
    import Database from '@lucide/svelte/icons/database';
    import { getKnowledgeBases, type KnowledgeBase } from '$lib/api/knowledgebase';
    import { getLanguages, type Language } from '$lib/api/languages';
    import * as Select from '$lib/components/ui/select/index.js';
    
    // State for centered input (similar to /chat)
    let inputValue = '';
    let textarea: HTMLTextAreaElement;
    let isInputEmpty = true;
    let isCreating = false;
    let ws: WebSocket | null = null;
    // Update isConnected status reactively based on WebSocket state
    $: isConnected = ws?.readyState === WebSocket.OPEN;
    let recording = false;

    let isLoading = false;
    let recordingLoading = false;
    
    // File upload state
    let showFileUpload = false;
    let selectedFiles: File[] = [];
    let fileInput: HTMLInputElement;
    
    // Knowledge base state
    let knowledgeBases: KnowledgeBase[] = [];
    let selectedKnowledgeBase: string = "";
    
    // Language selection state
    let languages: Language[] = [];
    let selectedLanguageId: string | null = null;  // UUID of selected language
    
    // Disclaimer modal
    let showDisclaimerModal = false;
    
    // File processing state
    let processingFiles: number[] = [];
    let fileProcessingStatus: { [fileId: number]: string } = {};
    let checkingFileStatus = false;
    
    // Admin check
    let isAdmin = false;
    $: isAdmin = $user?.is_superuser || $user?.is_staff || false;
    
    // Reactive stores
    const connectionStatus = writable<'connecting' | 'connected' | 'disconnected'>('disconnected');

    // Get chat ID from URL if present
    let urlChatId: string | undefined;
    $: urlChatId = $page.url.pathname.match(/\/c\/(\d+)$/)?.[1];
    
    // Update isInputEmpty reactively - must have text input to submit
    $: isInputEmpty = inputValue.trim() === '';

    onMount(() => {
        if (browser) {
            console.log('[Main Chat Page] Mounting, URL path:', $page.url.pathname);
            
            // If this is a specific chat page (/c/:id), don't initialize here
            // Let the /c/[id]/+page.svelte handle it to prevent race conditions
            if (urlChatId) {
                console.log('[Main Chat Page] Detected /c/:id route, skipping initialization - [id]/+page.svelte will handle it');
                return;
            }
            
            // Initialize settings for file validation
            initializeSettings().catch(error => {
                console.warn('Failed to initialize settings:', error);
            });
            
            // Load knowledge bases
            getKnowledgeBases().then(kbs => {
                knowledgeBases = kbs;
                console.log('Loaded knowledge bases:', knowledgeBases);
            }).catch(error => {
                console.error('Error loading knowledge bases:', error);
            });
            
            // Load languages
            getLanguages().then(langs => {
                languages = langs;
                // Set default to first language (usually English)
                if (langs.length > 0) {
                    selectedLanguageId = langs[0].id;
                }
                console.log('Loaded languages:', languages);
            }).catch(error => {
                console.error('Error loading languages:', error);
            });
            
            console.log('[Main Chat Page] On main chat page, ready for user input');
            // Don't connect WebSocket immediately for new chats - wait for user to send message
        }
    });

    onDestroy(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close(1000, 'Component destroyed'); // Use code 1000 for normal closure
        }
    });

    function connectWebSocket(): Promise<void> {
        return new Promise((resolve, reject) => {
            // Don't create a new connection if one already exists and is connected
            if (ws && ws.readyState === WebSocket.OPEN) {
                console.log('WebSocket already connected');
                resolve();
                return;
            }

            // Close existing connection if it exists
            if (ws) {
                ws.close();
            }

            // Get auth token from store
            const token = get(authToken);
            if (!token) {
                console.error('No auth token available for WebSocket connection');
                connectionStatus.set('disconnected');
                reject(new Error('No auth token'));
                return;
            }

            // Build WebSocket URL for new chat - include KB so backend can create chat with it
            let wsUrl = `${WEBSOCKET_BASE_URL}/ws/chat/?token=${token}`;
            if (selectedKnowledgeBase) {
                wsUrl += `&knowledge_base_id=${selectedKnowledgeBase}`;
            }
            console.log('Connecting for new chat WebSocket, backend will create chat on first message. KB:', selectedKnowledgeBase);
            
            console.log('WebSocket URL:', wsUrl);
            connectionStatus.set('connecting');
            ws = new WebSocket(wsUrl);

            const timeout = setTimeout(() => {
                reject(new Error('Connection timeout'));
                ws?.close();
            }, 10000);

            ws.onopen = () => {
                clearTimeout(timeout);
                connectionStatus.set('connected');
                console.log('WebSocket connected successfully');
                console.log('WebSocket readyState:', ws?.readyState);
                console.log('WebSocket OPEN constant:', WebSocket.OPEN);
                resolve();
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            ws.onclose = (event) => {
                clearTimeout(timeout);
                connectionStatus.set('disconnected');
                console.log('WebSocket disconnected:', event.code, event.reason);
            };

            ws.onerror = (error) => {
                clearTimeout(timeout);
                console.error('WebSocket error:', error);
                console.log('Failed to connect to:', wsUrl);
                connectionStatus.set('disconnected');
                reject(error);
            };
        });
    }

    function handleWebSocketMessage(data: any) {
        console.log('[Main Chat Page] Received WebSocket message:', data);
        
        if (data.type === 'message') {
            const message = data.message;
            
            // Handle chat navigation - redirect to the new chat page
            if (message.chat_id) {
                console.log('[Main Chat Page] Redirecting to new chat:', message.chat_id);
                goto(`/c/${message.chat_id}`);
            }
        } else if (data.type === 'loading') {
            isLoading = data.loading;
            console.log('[Main Chat Page] Loading state changed:', isLoading);
        } else if (data.type === 'error') {
            console.log('[Main Chat Page] Received error from WebSocket:', data);
            
            // Stop loading immediately
            isLoading = false;
            
            // Show toast notification
            toast.error(data.message || data.error || 'An error occurred', {
                duration: 5000,
                dismissible: true,
                closeButton: true
            });
        }
    }

    function resizeTextarea(textareaEl: HTMLTextAreaElement) {
        textareaEl.style.height = 'auto';
        const scrollHeight = textareaEl.scrollHeight;
        const minHeight = 30;
        const maxHeight = 320;

        if (scrollHeight <= maxHeight) {
            textareaEl.style.height = Math.max(scrollHeight, minHeight) + 'px';
            textareaEl.style.overflowY = 'hidden';
        } else {
            textareaEl.style.height = maxHeight + 'px';
            textareaEl.style.overflowY = 'auto';
        }
    }

    function handleInput(event: Event) {
        resizeTextarea(event.target as HTMLTextAreaElement);
    }

    // File processing status polling
    async function pollFileStatus(fileIds: number[]) {
        if (fileIds.length === 0 || checkingFileStatus) return;
        
        console.log('Starting file status polling for files:', fileIds);
        checkingFileStatus = true;
        const maxAttempts = 60; // 5 minutes max (5s * 60)
        let attempts = 0;
        
        const poll = async () => {
            try {
                attempts++;
                console.log(`Polling attempt ${attempts}/${maxAttempts} for files:`, fileIds);
                const statusList = await newChatApi.checkFileStatus(fileIds);
                console.log('File status response:', statusList);
                
                // Update file status
                statusList.forEach(file => {
                    fileProcessingStatus[file.id] = file.status;
                    console.log(`File ${file.id} (${file.file_name}): ${file.status}`);
                });
                
                // Check if all files are completed or failed
                const allCompleted = statusList.every(file => 
                    file.status === 'COMPLETED' || file.status === 'FAILED'
                );
                
                console.log('All files completed?', allCompleted, 'Status list:', statusList.map(f => f.status));
                
                if (allCompleted || attempts >= maxAttempts) {
                    // All files processed or timeout
                    processingFiles = [];
                    checkingFileStatus = false;
                    
                    if (allCompleted) {
                        const failedFiles = statusList.filter(file => file.status === 'FAILED');
                        if (failedFiles.length > 0) {
                            console.error('Failed files:', failedFiles);
                            
                            // Show detailed error messages for each failed file
                            failedFiles.forEach(file => {
                                let errorMessage = `File "${file.file_name}" failed to process`;
                                
                                // Check if there's a detailed error message in other_info
                                if (file.other_info && file.other_info.message) {
                                    errorMessage = file.other_info.message;
                                } else if (file.other_info && file.other_info.error) {
                                    errorMessage = `${file.file_name}: ${file.other_info.error}`;
                                }
                                
                                toast.error(errorMessage, {
                                    duration: 8000  // Show error for 8 seconds
                                });
                            });
                        } else {
                            console.log('All files processed successfully');
                        }
                    } else {
                        console.error('File processing timeout after', maxAttempts, 'attempts');
                        toast.error('File processing timeout. Please try again.');
                    }
                } else {
                    // Continue polling
                    setTimeout(poll, 5000); // Poll every 5 seconds
                }
            } catch (error) {
                console.error('Error polling file status:', error);
                checkingFileStatus = false;
                processingFiles = [];
            }
        };
        
        poll();
    }

    // Check if user can send messages (no files processing)
    $: canSendMessage = processingFiles.length === 0;
    
    // Check if user has selected KB or attached files (required to send message)
    $: hasKBOrFiles = selectedKnowledgeBase !== "" || selectedFiles.length > 0;
    
    // Can submit: must have text, no processing, and either KB selected or files attached
    $: canSubmit = !isInputEmpty && canSendMessage && hasKBOrFiles;

    async function startNewConversation(event?: Event) {
        if (event) {
            event.preventDefault();
        }
        
        if (isInputEmpty || isCreating) return;
        
        // Validate that user has either selected KB or attached files (or both)
        if (!hasKBOrFiles) {
            toast.error('Please select a Report/Manual and/or attach a document before sending your message.', {
                duration: 5000,
                dismissible: true,
                closeButton: true
            });
            return;
        }

        const messageText = inputValue.trim();
        const filesToUpload = [...selectedFiles];
        
        if (!messageText && filesToUpload.length === 0) return;

        isCreating = true;
        
        // Clear input and files immediately
        inputValue = '';
        selectedFiles = [];

        try {
            // Set loading immediately when starting conversation
            isLoading = true;
            
            // FLOW 1: If we have files, upload them first (API call)
            if (filesToUpload.length > 0) {
                console.log('Flow 1: Uploading files and getting chat_id');
                const kbId = selectedKnowledgeBase ? parseInt(selectedKnowledgeBase) : null;
                const result = await newChatApi.uploadFilesToChat(filesToUpload, messageText, null, kbId, selectedLanguageId);
                
                if (result.success && result.chat_id) {
                    const chatId = result.chat_id;
                    console.log('Got chat_id from file upload:', chatId);
                    
                    // Redirect to the chat page - it will handle WebSocket connection and start polling
                    goto(`/c/${chatId}`);
                    return;
                }
            }
            
            // FLOW 2: No files, just message - connect WebSocket and send
            else {
                console.log('Flow 2: No files, connecting WebSocket for message');
                
                // Ensure WebSocket is connected - this is where we connect for new chats
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    console.log('Connecting WebSocket for new chat...');
                    await connectWebSocket();
                    // Small delay to ensure connection is fully established
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                
                console.log('WebSocket state before sending:', {
                    exists: !!ws,
                    readyState: ws?.readyState,
                    OPEN: WebSocket.OPEN
                });
                
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    throw new Error(`Failed to establish WebSocket connection. State: ${ws?.readyState}`);
                }
                
                // Send message via WebSocket - backend will return chat_id
                const messageData = {
                    message: messageText,
                    chat_id: null, // null means create new chat
                    language_id: selectedLanguageId
                };
                
                console.log('Sending new chat message via WebSocket:', messageData);
                try {
                    ws.send(JSON.stringify(messageData));
                    console.log('Message sent successfully via WebSocket');
                } catch (wsError) {
                    console.error('WebSocket send error:', wsError);
                    throw new Error(`WebSocket send failed: ${wsError.message}`);
                }
                // WebSocket response will contain chat_id, we'll redirect in handleWebSocketMessage
            }
            
        } catch (error) {
            console.error('Error starting conversation:', error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack,
                wsState: ws?.readyState,
                wsUrl: ws?.url
            });
            // Reset input on error
            inputValue = messageText;
            selectedFiles = filesToUpload;
            isLoading = false;
            
            // Only show toast if it's not a validation error (those are already shown by the API)
            if (!error.message?.includes('Daily chat limit') && !error.message?.includes('daily chat limit')) {
                toast.error(`Error sending message: ${error.message}. Please try again.`, {
                    duration: Infinity,
                    dismissible: true,
                    closeButton: true
                });
            }
        } finally {
            isCreating = false;
        }
    }

    function handleKeyDown(event: KeyboardEvent) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            startNewConversation();
        } else if (event.key === 'Tab') {
            event.preventDefault();
            insertTextAtCursor('\t', event.target as HTMLTextAreaElement);
        }
    }

    // Voice recording functions
    function insertTextAtCursor(text: string, textareaEl?: HTMLTextAreaElement) {
        const el = textareaEl ?? textarea;
        if (!el) {
            inputValue += text;
            return;
        }

        const start = el.selectionStart ?? el.value.length;
        const end = el.selectionEnd ?? start;
        inputValue = inputValue.slice(0, start) + text + inputValue.slice(end);

        requestAnimationFrame(() => {
            const pos = start + text.length;
            el.setSelectionRange(pos, pos);
            el.focus();
            resizeTextarea(el);
        });
    }

    async function startVoiceRecording() {
        recordingLoading = true;
        try {
            // Request microphone permission
            let stream = await navigator.mediaDevices
                .getUserMedia({ audio: true })
                .catch(function (err) {
                    toast.error(`Permission denied when accessing microphone: ${err}`);
                    recordingLoading = false;
                    return null;
                });

            if (stream) {
                // Permission granted, start recording
                recording = true;
                // Keep recordingLoading true until recording actually starts
                const tracks = stream.getTracks();
                tracks.forEach((track) => track.stop());
            }
            
            if (!stream) {
                recordingLoading = false;
            }
            
            stream = null;
        } catch {
            toast.error('Permission denied when accessing microphone');
            recordingLoading = false;
        }
    }

    function onVoiceRecordingStarted() {
        recordingLoading = false;
    }

    function onVoiceRecordingCancel() {
        recording = false;
        recordingLoading = false;
    }

    function onVoiceRecordingConfirm(data: any) {
        const { text } = data.detail;
        recording = false;
        recordingLoading = false;
        insertTextAtCursor(text);
    }

    // File upload functions
    function toggleFileUpload() {
        if (!canSendMessage) return; // Prevent file selection during processing
        
        if (showFileUpload) {
            // If closing, clear selected files and reset
            selectedFiles = [];
            showFileUpload = false;
        } else {
            // If opening, trigger file picker
            fileInput?.click();
        }
    }

    function handleFileSelection(event: Event) {
        const target = event.target as HTMLInputElement;
        const files = target.files;
        
        if (files && files.length > 0) {
            const fileArray = Array.from(files);
            
            const totalFiles = selectedFiles.length + fileArray.length;
            if (totalFiles > 5) {
                toast.error('Maximum 5 files allowed');
                return;
            }
            
            // Validate file types including double extension check
            const invalidTypeFiles = fileArray.filter(file => !validateFileType(file));
            if (invalidTypeFiles.length > 0) {
                invalidTypeFiles.forEach(file => {
                    toast.error(`Invalid or unsafe file: ${file.name}`);
                });
                target.value = '';
                return;
            }
            
            // Validate file sizes using dynamic settings
            const { validFiles, errors } = validateFiles(fileArray);
            
            if (errors.length > 0) {
                showFileValidationErrors(errors);
                target.value = '';
                return;
            }
            
            selectedFiles = [...selectedFiles, ...validFiles];
            target.value = '';
        }
    }

    function removeFile(index: number) {
        selectedFiles = selectedFiles.filter((_, i) => i !== index);
    }

    function clearAllFiles() {
        selectedFiles = [];
    }

    function showDisclaimer() {
        showDisclaimerModal = true;
    }
</script>

<svelte:head>
    <title>Chat - MOSPI</title>
</svelte:head>

<!-- Only render this page content when on the main /c route -->
<!-- When on /c/:id, this component is mounted but shouldn't interfere -->
{#if !urlChatId}
    <!-- Initial Centered Input (like /chat) -->
    <div class="relative h-full flex flex-col items-center justify-center overflow-hidden">
        <div class="absolute right-4 top-4 z-10 sm:right-6 sm:top-6">
            <Tooltip.Root>
                <Tooltip.Trigger>
                    <button
                        type="button"
                        class="text-xs font-medium text-primary border border-primary/40 rounded-md px-2.5 py-1 hover:bg-primary/5 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors"
                        aria-label="Help for requesting a missing document"
                    >
                        Didn't find the document?
                    </button>
                </Tooltip.Trigger>
                <Tooltip.Content side="bottom" align="end" class="max-w-sm text-left">
                    <p class="text-xs leading-relaxed">
                        Please send the documents published by MoSPI to di.lab@mospi.gov.in with the subject line "Request for Knowledge Update for MoSPI StatsDoc Chatbot". The submitted documents will be reviewed and incorporated into the chatbot's knowledge base within 2 working days.
                    </p>
                </Tooltip.Content>
            </Tooltip.Root>
        </div>
        <div class="w-full max-w-2xl mx-auto px-4">
            <!-- Welcome Message Section -->
            <div class="w-full flex justify-center mb-8">
                <div class="text-center">
                    <h1 class="text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
                        I am MoSPI StatsDoc AI Assistant
                    </h1>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        Select document and start conversation with that!
                    </p>
                </div>
            </div>
            
            <!-- Centered Input Area -->
            <div class="w-full flex justify-center">
                <div class="w-full">
                    {#if recording}
                        <VoiceRecording
                            bind:recording
                            on:started={onVoiceRecordingStarted}
                            on:cancel={onVoiceRecordingCancel}
                            on:confirm={onVoiceRecordingConfirm}
                        />
                    {:else}
                        <input 
                            type="file" 
                            bind:this={fileInput}
                            on:change={handleFileSelection}
                            multiple 
                            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                            hidden
                        >
                        <form class="w-full flex flex-col gap-1.5" on:submit|preventDefault={startNewConversation}>
                            <div class="flex-1 flex flex-col relative w-full shadow-lg rounded-3xl transition px-1 bg-white/90 dark:bg-gray-400/5 dark:text-gray-100" dir="auto">
                                <!-- Selected Files Display -->
                                {#if selectedFiles.length > 0}
                                    <div class="px-3 pt-2.5 pb-1">
                                        <div class="flex flex-wrap gap-1.5">
                                            {#each selectedFiles as file, index (file.name + index)}
                                                <FileChip 
                                                    {file} 
                                                    onRemove={() => removeFile(index)} 
                                                />
                                            {/each}
                                        </div>
                                    </div>
                                {/if}
                                
                                <!-- File processing status -->
                                {#if processingFiles.length > 0}
                                    <div class="px-2.5 py-2">
                                        <div class="text-sm text-blue-600 dark:text-blue-400 flex items-center gap-2">
                                            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                            <span>Processing {processingFiles.length} file{processingFiles.length > 1 ? 's' : ''}...</span>
                                        </div>
                                        <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                            Please wait before sending your next message.
                                        </div>
                                    </div>
                                {/if}
                                
                                <div class="px-2.5">
                                    <div class="scrollbar-hidden rtl:text-right ltr:text-left bg-transparent dark:text-gray-100 outline-hidden w-full pt-2.5 pb-[5px] px-1 resize-none h-fit max-h-80 overflow-auto" id="chat-input-container">
                                        <div class="relative w-full min-w-full h-full min-h-fit input-prose">
                                            <textarea
                                                placeholder={processingFiles.length > 0 ? "Processing files..." : !hasKBOrFiles ? "Select a Report/Manual and/or attach a document first..." : "How can I help you today?"}
                                                class="w-full resize-none text-base text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 bg-transparent border-none outline-none font-normal min-h-[30px] max-h-80 pr-2 pt-3 scrollbar-hidden"
                                                style="font-family: system-ui, sans-serif; overflow-y: hidden;"
                                                bind:value={inputValue}
                                                on:input={handleInput}
                                                on:keydown={handleKeyDown}
                                                bind:this={textarea}
                                                disabled={isCreating || !canSendMessage}
                                            ></textarea>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="flex justify-between mt-0.5 mb-2.5 mx-0.5 max-w-full" dir="ltr">
                                    <div class="ml-1 self-end flex items-center gap-2 flex-1 max-w-[80%]">
                                        {#if isAdmin}
                                            <Tooltip.Root>
                                                <Tooltip.Trigger>
                                                    <button type="button" class="flex items-center gap-1.5 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-800 dark:text-white rounded-full py-1.5 px-2.5 outline-hidden focus:outline-hidden transition-all {!canSendMessage ? 'opacity-50 cursor-not-allowed' : ''}" on:click={toggleFileUpload} disabled={!canSendMessage}>
                                                        <Paperclip class="size-4 transition-transform text-gray-600 dark:text-gray-300" />
                                                        <span class="text-xs font-medium text-gray-600 dark:text-gray-400">Attach</span>
                                                    </button>
                                                </Tooltip.Trigger>
                                                <Tooltip.Content side="top" align="center" class="max-w-xs">
                                                    <p class="text-sm">Upload Image, PDF/Word File of 20 MB or less and ask the questions to get the response from the context of the document.</p>
                                                </Tooltip.Content>
                                            </Tooltip.Root>
                                        {/if}
                        <!-- Report/Manual Selector -->
                        <div class="relative max-w-[120px] sm:max-w-[180px] md:max-w-none">
                            <select 
                                bind:value={selectedKnowledgeBase}
                                class="flex items-center gap-1.5 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-700 rounded-full py-1.5 pl-8 pr-3 outline-none focus:outline-none transition-all border border-gray-200 dark:border-gray-700 text-xs font-medium cursor-pointer appearance-none w-full truncate"
                            >
                                <option value="">Select Report/Manual</option>
                                {#each knowledgeBases as kb}
                                    <option value={kb.id.toString()}>{kb.name}</option>
                                {/each}
                            </select>
                            <Database class="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-gray-600 dark:text-gray-300 pointer-events-none" />
                        </div>                                        <!-- Language Selector -->
                                        <div class="relative max-w-[120px] sm:max-w-[180px] md:max-w-none">
                                            <select 
                                                bind:value={selectedLanguageId}
                                                class="flex items-center gap-1.5 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-700 rounded-full py-1.5 pl-8 pr-3 outline-none focus:outline-none transition-all border border-gray-200 dark:border-gray-700 text-xs font-medium cursor-pointer appearance-none w-full truncate"
                                            >
                                                {#each languages as lang}
                                                    <option value={lang.id}>{lang.name}</option>
                                                {/each}
                                            </select>
                                            <img src="/language.svg" alt="language" class="absolute left-2.5 top-1/2 -translate-y-1/2 size-6 pointer-events-none" />
                                        </div>
                                    </div>

                                    <div class="self-end flex space-x-1 mr-1 shrink-0">
                                        <div class="flex">
                                            <button 
                                                id="voice-input-button" 
                                                class="text-gray-600 dark:text-gray-300 hover:text-gray-700 dark:hover:text-gray-200 transition rounded-full p-1.5 mr-0.5 self-center {recordingLoading || recording ? 'cursor-not-allowed opacity-50' : ''}" 
                                                type="button" 
                                                aria-label="Voice Input"
                                                on:click={startVoiceRecording}
                                                disabled={recordingLoading || recording}
                                            >
                                                {#if recordingLoading || (recording && recordingLoading)}
                                                    <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div>
                                                {:else}
                                                    <Mic class="w-5 h-5 translate-y-[0.5px]" />
                                                {/if}
                                            </button>
                                        </div>
                                        <div class="flex items-center">
                                            <div class="flex">
                                                <button 
                                                    id="send-message-button" 
                                                    class="text-white transition rounded-full p-1.5 self-center {!canSubmit || isCreating || isLoading ? 'bg-gray-200 dark:bg-gray-700 cursor-not-allowed' : 'bg-primary hover:bg-primary/90'}" 
                                                    type="submit" 
                                                    disabled={!canSubmit || isCreating || isLoading}
                                                >
                                                    {#if isCreating || isLoading}
                                                        <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                                    {:else}
                                                        <ArrowUp class="size-5" />
                                                    {/if}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="mb-1"></div>
                        </form>
                        
                        <!-- Disclaimer -->
                        <div class="mt-2 text-center">
                            <p class="text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                                The MoSPI StatsDoc AI Assistant is an AI system. This AI chatbot is designed to answer queries related to MoSPI documents that are selected while asking queries. For more accurate and relevant responses, users are encouraged to provide prompts with clarity and context. There may be different responses for same query as they are generated by Large Language Model that are probabilistic in nature. By accessing this service, users agree to the following 
                                <button class="text-blue-600 dark:text-blue-400 hover:underline underline" on:click={() => showDisclaimer()}>Disclaimer</button>.
                            </p>
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    </div>
{/if}

<!-- Disclaimer Modal -->
{#if showDisclaimerModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-modal="true" on:click={() => showDisclaimerModal = false} on:keydown={(e) => { if (e.key === 'Escape') showDisclaimerModal = false; }}>
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl mx-4 max-h-[80vh] overflow-y-auto" on:click|stopPropagation on:keydown|stopPropagation>
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold text-gray-900 dark:text-white">Disclaimer</h2>
                <button class="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white" aria-label="Close disclaimer" on:click={() => showDisclaimerModal = false}>
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            <div class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                <p class="mb-4">
                    The "MoSPI StatsDoc AI Assistant" is an Initiative of the Ministry of Statistics and Programme Implementation (MoSPI). The content and responses generated by this tool are intended solely to facilitate document search with the help of AI Enabled Intelligent Search.
                </p>
                <p class="mb-4">
                    This chatbot is powered by third-party Large Language Models (LLMs) and fine-tuned to improve the user experience by searching through documents semantically, and despite the implementation of safeguards and guardrails, the responses generated should not be taken as evidence or treated as official communication. MoSPI shall not be liable for any loss, damage, or consequence arising from the use of this AI system.
                </p>
                <p class="mb-4">
                    MoSPI makes no warranties regarding the accuracy, completeness, or reliability of the information provided. The Ministry and its staff, individually and collectively, shall not be liable for any financial or other consequences whatsoever arising from the use of this application, including but not limited to inappropriate, improper, or fraudulent use. Users are strongly cautioned to verify the accuracy and completeness of any information before relying on it for decision-making or any other purpose.
                </p>
            </div>
        </div>
    </div>
{/if}

<style>
    :global(.prose table) {
        font-size: 0.75rem;
        border-collapse: collapse;
        width: 100%;
    }
    
    :global(.prose th),
    :global(.prose td) {
        border: 1px solid #e5e7eb;
        padding: 0.25rem 0.5rem;
        text-align: left;
    }
    
    :global(.prose th) {
        background-color: #f9fafb;
        font-weight: 600;
    }

    :global(.dark .prose th) {
        background-color: #374151;
        border-color: #4b5563;
    }

    :global(.dark .prose td) {
        border-color: #4b5563;
    }

    /* Chart container styling */
    :global(.chart-container) {
        width: 100%;
        max-width: 100%;
        overflow: hidden;
    }

    :global(.chart-container svg) {
        max-width: 100%;
        height: auto;
    }

    :global(.chart-container div[id^="plotly"]) {
        max-width: 100% !important;
        width: 100% !important;
    }

    :global(.chart-container .plotly-graph-div) {
        max-width: 100% !important;
        width: 100% !important;
    }
</style>

