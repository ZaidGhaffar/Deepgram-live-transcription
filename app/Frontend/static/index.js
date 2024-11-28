class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioContext = null;
        this.audioStream = null;
        this.websocket = null;
        this.isRecording = false;
        this.processorNode = null;

        // DOM elements
        this.startButton = document.getElementById('startButton');
        this.stopButton = document.getElementById('stopButton');
        this.status = document.getElementById('status');
        this.transcription = document.getElementById('transcription');

        // Bind event listeners
        this.startButton.addEventListener('click', () => this.startRecording());
        this.stopButton.addEventListener('click', () => this.stopRecording());

        // Debug flag
        this.debug = true;
    }

    log(message) {
        if (this.debug) {
            console.log(`[AudioRecorder] ${message}`);
        }
    }

    async initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            this.log('WebSocket connection established');
            this.updateStatus('Connected to server');
        };

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.log('Received message:', data);
            
            if (data.transcription) {
                this.updateTranscription(data.transcription);
            } else if (data.error) {
                this.updateStatus(`Error: ${data.error}`);
                console.error('Server error:', data.error);
            } else if (data.status === 'disconnected') {
                this.updateStatus('Disconnected from server');
            }
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateStatus('WebSocket error occurred');
        };

        this.websocket.onclose = () => {
            this.log('WebSocket connection closed');
            this.updateStatus('Disconnected from server');
        };

        // Wait for the connection to be established
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('WebSocket connection timeout'));
            }, 5000);

            this.websocket.onopen = () => {
                clearTimeout(timeout);
                resolve();
            };

            this.websocket.onerror = (error) => {
                clearTimeout(timeout);
                reject(error);
            };
        });
    }

    async startRecording() {
        try {
            this.log('Starting recording...');
            
            // Initialize audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });

            // Get microphone stream
            this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            this.log('Got audio stream');

            // Initialize WebSocket
            await this.initializeWebSocket();
            this.log('WebSocket initialized');

            // Create audio nodes
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);

            // Connect nodes
            source.connect(this.processorNode);
            this.processorNode.connect(this.audioContext.destination);

            // Process audio
            this.processorNode.onaudioprocess = (e) => {
                if (this.websocket?.readyState === WebSocket.OPEN) {
                    const inputData = e.inputBuffer.getChannelData(0);
                    const audio16 = new Int16Array(inputData.length);
                    
                    // Convert float32 to int16
                    for (let i = 0; i < inputData.length; i++) {
                        const s = Math.max(-1, Math.min(1, inputData[i]));
                        audio16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                    }
                    
                    this.log(`Sending audio chunk of size: ${audio16.length}`);
                    this.websocket.send(audio16.buffer);
                }
            };

            this.isRecording = true;
            this.updateStatus('Recording... Speak now!');
            this.startButton.disabled = true;
            this.stopButton.disabled = false;
            this.log('Recording started');

        } catch (error) {
            console.error('Error starting recording:', error);
            this.updateStatus(`Error: ${error.message}`);
            this.stopRecording();
        }
    }

    stopRecording() {
        this.log('Stopping recording...');
        
        if (this.isRecording) {
            // Stop audio processing
            if (this.processorNode) {
                this.processorNode.disconnect();
                this.processorNode = null;
            }
            
            if (this.audioContext) {
                this.audioContext.close();
                this.audioContext = null;
            }
            
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
                this.audioStream = null;
            }
            
            // Close WebSocket
            if (this.websocket) {
                this.websocket.close();
                this.websocket = null;
            }
            
            this.isRecording = false;
            this.updateStatus('Recording stopped');
            this.startButton.disabled = false;
            this.stopButton.disabled = true;
            this.log('Recording stopped');
        }
    }

    updateStatus(message) {
        this.status.textContent = message;
        this.log(`Status updated: ${message}`);
    }

    updateTranscription(text) {
        if (text && text.trim()) {
            // Create a new paragraph for each transcription
            const p = document.createElement('p');
            p.textContent = text;
            
            // Add the new transcription to the top
            this.transcription.insertBefore(p, this.transcription.firstChild);
            
            // Keep only the last 10 transcriptions
            while (this.transcription.children.length > 10) {
                this.transcription.removeChild(this.transcription.lastChild);
            }
            
            this.log(`Transcription updated: ${text}`);
        }
    }
}

// Initialize the audio recorder when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new AudioRecorder();
});