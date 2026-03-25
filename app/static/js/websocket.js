/**
 * OrderPulse — WebSocket Module
 * Manages SocketIO connection for real-time task progress updates.
 */

OrderPulse.WS = OrderPulse.WS || {};
OrderPulse.WS.connected = false;

(function () {
    let socket = null;

    OrderPulse.WS.init = function () {
        try {
            socket = io({
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 10,
                reconnectionDelay: 2000
            });

            socket.on('connect', () => {
                OrderPulse.WS.connected = true;
                updateConnectionUI(true);
                console.log('[OrderPulse WS] Connected');
            });

            socket.on('disconnect', () => {
                OrderPulse.WS.connected = false;
                updateConnectionUI(false);
                console.log('[OrderPulse WS] Disconnected');
            });

            socket.on('connected', (data) => {
                console.log('[OrderPulse WS] Server says:', data.message);
            });

            // Real-time task progress
            socket.on('task_progress', (data) => {
                handleTaskProgress(data);
            });

            socket.on('connect_error', (err) => {
                OrderPulse.WS.connected = false;
                updateConnectionUI(false);
                console.warn('[OrderPulse WS] Connection error:', err.message);
            });

        } catch (e) {
            console.warn('[OrderPulse WS] Failed to initialize:', e);
            updateConnectionUI(false);
        }
    };

    function handleTaskProgress(data) {
        const { task_id, progress, message } = data;

        // Only update if this is our current task
        if (OrderPulse._currentTaskId && task_id === OrderPulse._currentTaskId) {
            if (progress >= 0 && progress <= 100) {
                OrderPulse._updateProgress(progress, message);
            }

            if (progress === 100) {
                // Task completed — load results
                OrderPulse.showToast('Orders loaded successfully!', 'success');
                OrderPulse._loadReport();
            } else if (progress === -1) {
                // Task failed or cancelled
                const isCancel = message && message.toLowerCase().includes('cancel');
                OrderPulse.showToast(message || 'Task ended.', isCancel ? 'warning' : 'error');
                OrderPulse._resetLoadUI();
            }
        }
    }

    function updateConnectionUI(isConnected) {
        const statusIcon = document.querySelector('#connectionStatus .status-icon');
        const statusText = document.querySelector('#connectionStatus .status-text');

        if (statusIcon) {
            statusIcon.classList.toggle('connected', isConnected);
        }
        if (statusText) {
            statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
        }
    }

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', () => {
        OrderPulse.WS.init();
    });

})();

