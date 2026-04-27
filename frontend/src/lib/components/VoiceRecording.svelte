<script lang="ts">
	import { tick, createEventDispatcher } from 'svelte';
	import { X } from 'lucide-svelte';
	import { speechApi } from '$lib/api/speech.js';
	import { toast } from 'svelte-sonner';
	
	const dispatch = createEventDispatcher();

	export let recording = false;
	export let transcribe = true;
	export let className = ' p-2.5 w-full max-w-full';

	let loading = false;
	let processing = false;
	let transcribing = false;
	let confirmed = false;
	let durationSeconds = 0;
	let durationCounter: number | null = null;
	let transcription = '';
	let isStopping = false; // Flag to track intentional stopping

	// Audio related variables
	let stream: MediaStream | null = null;
	let mediaRecorder: MediaRecorder | null = null;
	let audioChunks: Blob[] = [];

	// Visualizer configuration
	const MIN_DECIBELS = -45;
	let VISUALIZER_BUFFER_LENGTH = 300;
	let visualizerData: number[] = Array(VISUALIZER_BUFFER_LENGTH).fill(0);

	const startDurationCounter = () => {
		durationCounter = setInterval(() => {
			durationSeconds++;
		}, 1000);
	};

	const stopDurationCounter = () => {
		if (durationCounter) {
			clearInterval(durationCounter);
		}
		durationSeconds = 0;
	};

	const formatSeconds = (seconds: number) => {
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = seconds % 60;
		const formattedSeconds = remainingSeconds < 10 ? `0${remainingSeconds}` : remainingSeconds;
		return `${minutes}:${formattedSeconds}`;
	};

	// Function to calculate the RMS level from time domain data
	const calculateRMS = (data: Uint8Array) => {
		let sumSquares = 0;
		for (let i = 0; i < data.length; i++) {
			const normalizedValue = (data[i] - 128) / 128; // Normalize the data
			sumSquares += normalizedValue * normalizedValue;
		}
		return Math.sqrt(sumSquares / data.length);
	};

	const normalizeRMS = (rms: number) => {
		rms = rms * 10;
		const exp = 1.5; // Adjust exponent value; values greater than 1 expand larger numbers more and compress smaller numbers more
		const scaledRMS = Math.pow(rms, exp);

		// Scale between 0.01 (1%) and 1.0 (100%)
		return Math.min(1.0, Math.max(0.01, scaledRMS));
	};

	const analyseAudio = (audioStream: MediaStream) => {
		const audioContext = new AudioContext();
		const audioStreamSource = audioContext.createMediaStreamSource(audioStream);

		const analyser = audioContext.createAnalyser();
		analyser.minDecibels = MIN_DECIBELS;
		audioStreamSource.connect(analyser);

		const bufferLength = analyser.frequencyBinCount;
		const domainData = new Uint8Array(bufferLength);
		const timeDomainData = new Uint8Array(analyser.fftSize);

		const detectSound = () => {
			const processFrame = () => {
				if (!recording || loading || processing || transcribing) return;

				if (recording && !loading && !processing && !transcribing) {
					analyser.getByteTimeDomainData(timeDomainData);
					analyser.getByteFrequencyData(domainData);

					// Calculate RMS level from time domain data
					const rmsLevel = calculateRMS(timeDomainData);
					// Push the calculated decibel level to visualizerData
					visualizerData.push(normalizeRMS(rmsLevel));

					// Ensure visualizerData array stays within the buffer length
					if (visualizerData.length >= VISUALIZER_BUFFER_LENGTH) {
						visualizerData.shift();
					}

					visualizerData = visualizerData;
				}

				requestAnimationFrame(processFrame);
			};

			requestAnimationFrame(processFrame);
		};

		detectSound();
	};

	const blobToFile = (blob: Blob, filename: string): File => {
		return new File([blob], filename, { type: blob.type });
	};

	const transcribeWithWhisper = async (audioBlob: Blob): Promise<string> => {
		try {
			transcribing = true;
			
			const transcribedText = await speechApi.transcribe(audioBlob);
			
			console.log('Whisper transcription result:', transcribedText);
			return transcribedText || '';
		} catch (error) {
			console.error('Whisper transcription error:', error);
			toast.error('Failed to transcribe audio. Please try again.');
			return '';
		} finally {
			transcribing = false;
		}
	};

	const onStopHandler = async (audioBlob: Blob, ext: string = 'webm') => {
		await tick();
		processing = true;
		
		const file = blobToFile(audioBlob, `Recording-${new Date().toLocaleString()}.${ext}`);

		if (transcribe) {
			const whisperTranscription = await transcribeWithWhisper(audioBlob);
			
			if (whisperTranscription && whisperTranscription.trim()) {
				transcription = whisperTranscription.trim();
				dispatch('confirm', {
					text: transcription,
					filename: file.name
				});
			} else {
				// If transcription failed or is empty, still provide the audio file
				dispatch('confirm', {
					file: file,
					blob: audioBlob
				});
			}
		} else {
			dispatch('confirm', {
				file: file,
				blob: audioBlob
			});
		}
		
		processing = false;
	};

	const startRecording = async () => {
		loading = true;
		transcription = '';

		try {
			stream = await navigator.mediaDevices.getUserMedia({
				audio: {
					echoCancellation: true,
					noiseSuppression: true,
					autoGainControl: true
				}
			});
		} catch (err) {
			console.error('Error accessing media devices.', err);
			toast.error('Error accessing media devices.');
			loading = false;
			recording = false;
			return;
		}

		const mimeTypes = ['audio/webm; codecs=opus', 'audio/mp4'];

		mediaRecorder = new MediaRecorder(stream, {
			mimeType: mimeTypes.find((type) => MediaRecorder.isTypeSupported(type))
		});

		mediaRecorder.onstart = () => {
			console.log('Recording started');
			loading = false;
			startDurationCounter();
			audioChunks = [];
			analyseAudio(stream!);
			// Dispatch event to parent that recording has actually started
			dispatch('started');
		};

		mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);

		mediaRecorder.onstop = async () => {
			console.log('Recording stopped');

			if (confirmed) {
				// Use the actual type provided by MediaRecorder
				let type = audioChunks[0]?.type || mediaRecorder!.mimeType || 'audio/webm';

				// split `/` and `;` to get the extension
				let ext = type.split('/')[1].split(';')[0] || 'webm';

				// If not audio, default to audio/webm
				if (!type.startsWith('audio/')) {
					ext = 'webm';
				}

				const audioBlob = new Blob(audioChunks, { type: type });
				await onStopHandler(audioBlob, ext);
				confirmed = false;
			}
			
			processing = false;
			transcribing = false;
			loading = false;
			audioChunks = [];
			recording = false;
		};

		try {
			mediaRecorder.start();
		} catch (error) {
			console.error('Error starting recording:', error);
			toast.error('Error starting recording.');
			loading = false;
			recording = false;
			return;
		}
	};

	const stopRecording = async () => {
		isStopping = true; // Set flag to indicate intentional stopping
		
		if (recording && mediaRecorder) {
			await mediaRecorder.stop();
		}

		stopDurationCounter();
		audioChunks = [];

		if (stream) {
			const tracks = stream.getTracks();
			tracks.forEach((track) => track.stop());
		}

		stream = null;
	};

	const confirmRecording = async () => {
		isStopping = true; // Set flag to indicate intentional stopping
		confirmed = true;

		// Stop media recorder which will trigger onstop and show processing state
		if (recording && mediaRecorder) {
			await mediaRecorder.stop();
		}

		stopDurationCounter();

		if (stream) {
			const tracks = stream.getTracks();
			tracks.forEach((track) => track.stop());
		}

		stream = null;
	};

	// Watch for recording state changes
	$: if (recording) {
		startRecording();
	} else {
		stopRecording();
	}
</script>

<div
	class="{loading || processing || transcribing
		? ' bg-gray-100/50 dark:bg-gray-850/50'
		: 'bg-indigo-300/10 dark:bg-indigo-500/10 '} rounded-full flex justify-between {className}"
>
	<div class="flex items-center mr-1">
		<button
			type="button"
			class="p-1.5

            {loading || processing || transcribing
				? ' bg-gray-200 dark:bg-gray-700/50'
				: 'bg-indigo-400/20 text-indigo-600 dark:text-indigo-300 '} 


             rounded-full"
			on:click={async () => {
				stopRecording();
				confirmed = false; // Reset confirmed flag on cancel
				dispatch('cancel');
			}}
			disabled={loading || processing || transcribing}
		>
			<X class="size-4" />
		</button>
	</div>

	<div
		class="flex flex-1 self-center items-center justify-between ml-2 mx-1 overflow-hidden h-6"
		dir="rtl"
	>
		<div
			class="flex items-center gap-0.5 h-6 w-full max-w-full overflow-hidden overflow-x-hidden flex-wrap"
		>
			{#each visualizerData.slice().reverse() as rms}
				<div class="flex items-center h-full">
					<div
						class="w-[2px] shrink-0
                    
                    {loading || processing || transcribing
							? ' bg-gray-500 dark:bg-gray-400   '
							: 'bg-indigo-500 dark:bg-indigo-400  '} 
                    
                    inline-block h-full"
						style="height: {Math.min(100, Math.max(14, rms * 100))}%;"
					/>
				</div>
			{/each}
		</div>
	</div>

	<div class="flex">
		<div class="mx-1.5 pr-1 flex justify-center items-center">
			<div
				class="text-sm
        
        
        {loading || processing || transcribing ? ' text-gray-500  dark:text-gray-400  ' : ' text-indigo-400 '} 
       font-medium flex-1 mx-auto text-center"
			>
				{#if transcribing}
					Transcribing...
				{:else if processing}
					Processing...
				{:else if loading}
					Starting...
				{:else}
					{formatSeconds(durationSeconds)}
				{/if}
			</div>
		</div>

		<div class="flex items-center">
			{#if loading || processing || transcribing}
				<div class=" text-gray-500 rounded-full cursor-not-allowed">
					<svg
						width="24"
						height="24"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
						fill="currentColor"
						><style>
							.spinner_OSmW {
								transform-origin: center;
								animation: spinner_T6mA 0.75s step-end infinite;
							}
							@keyframes spinner_T6mA {
								8.3% {
									transform: rotate(30deg);
								}
								16.6% {
									transform: rotate(60deg);
								}
								25% {
									transform: rotate(90deg);
								}
								33.3% {
									transform: rotate(120deg);
								}
								41.6% {
									transform: rotate(150deg);
								}
								50% {
									transform: rotate(180deg);
								}
								58.3% {
									transform: rotate(210deg);
								}
								66.6% {
									transform: rotate(240deg);
								}
								75% {
									transform: rotate(270deg);
								}
								83.3% {
									transform: rotate(300deg);
								}
								91.6% {
									transform: rotate(330deg);
								}
								100% {
									transform: rotate(360deg);
								}
							}
						</style><g class="spinner_OSmW"
							><rect x="11" y="1" width="2" height="5" opacity=".14" /><rect
								x="11"
								y="1"
								width="2"
								height="5"
								transform="rotate(30 12 12)"
								opacity=".29"
							/><rect
								x="11"
								y="1"
								width="2"
								height="5"
								transform="rotate(60 12 12)"
								opacity=".43"
							/><rect
								x="11"
								y="1"
								width="2"
								height="5"
								transform="rotate(90 12 12)"
								opacity=".57"
							/><rect
								x="11"
								y="1"
								width="2"
								height="5"
								transform="rotate(120 12 12)"
								opacity=".71"
							/><rect
								x="11"
								y="1"
								width="2"
								height="5"
								transform="rotate(150 12 12)"
								opacity=".86"
							/><rect x="11" y="1" width="2" height="5" transform="rotate(180 12 12)" /></g
						></svg
					>
				</div>
			{:else}
				<button
					type="button"
					class="p-1.5 bg-indigo-500 text-white dark:bg-indigo-500 dark:text-blue-950 rounded-full"
					on:click={async () => {
						console.log('Manual confirm clicked, processing transcription...');
						await confirmRecording();
					}}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="2.5"
						stroke="currentColor"
						class="size-4"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
					</svg>
				</button>
			{/if}
		</div>
	</div>
</div>
