"""Background task manager using ThreadPoolExecutor."""

import uuid
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from app import socketio

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages background tasks with progress tracking via SocketIO."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._tasks = {}
        self._cancel_flags = {}
        self._initialized = True

    def submit(self, func, *args, **kwargs):
        """
        Submit a background task.

        Returns:
            str: A unique task ID.
        """
        task_id = str(uuid.uuid4())[:8]
        self._cancel_flags[task_id] = threading.Event()

        def wrapper():
            try:
                self._tasks[task_id] = {'status': 'running', 'progress': 0, 'result': None}
                self._emit_progress(task_id, 0, 'Starting...')

                result = func(
                    task_id=task_id,
                    cancel_flag=self._cancel_flags[task_id],
                    *args,
                    **kwargs
                )

                if self._cancel_flags[task_id].is_set():
                    self._tasks[task_id]['status'] = 'cancelled'
                    self._emit_progress(task_id, -1, 'Task cancelled.')
                else:
                    self._tasks[task_id]['status'] = 'completed'
                    self._tasks[task_id]['result'] = result
                    self._emit_progress(task_id, 100, 'Completed!')

            except Exception as e:
                logger.error(f'Task {task_id} failed: {e}')
                self._tasks[task_id] = {
                    'status': 'failed',
                    'progress': -1,
                    'error': str(e)
                }
                self._emit_progress(task_id, -1, f'Error: {str(e)}')

        future = self._executor.submit(wrapper)
        self._tasks[task_id] = {'status': 'queued', 'progress': 0, 'future': future}
        logger.info(f'Task {task_id} submitted.')

        return task_id

    def cancel(self, task_id):
        """Signal a task to cancel."""
        if task_id in self._cancel_flags:
            self._cancel_flags[task_id].set()
            logger.info(f'Task {task_id} cancel signal sent.')
            return True
        return False

    def get_status(self, task_id):
        """Get the current status of a task."""
        task = self._tasks.get(task_id)
        if not task:
            return {'status': 'not_found'}
        return {
            'status': task.get('status', 'unknown'),
            'progress': task.get('progress', 0),
            'result': task.get('result'),
            'error': task.get('error')
        }

    def update_progress(self, task_id, progress, message=''):
        """Update task progress and emit via SocketIO."""
        if task_id in self._tasks:
            self._tasks[task_id]['progress'] = progress
        self._emit_progress(task_id, progress, message)

    def _emit_progress(self, task_id, progress, message):
        """Emit progress update via SocketIO."""
        try:
            socketio.emit('task_progress', {
                'task_id': task_id,
                'progress': progress,
                'message': message
            })
        except Exception as e:
            logger.warning(f'Failed to emit SocketIO event: {e}')


# Global task manager singleton
task_manager = TaskManager()
