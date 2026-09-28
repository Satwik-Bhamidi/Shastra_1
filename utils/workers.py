from PyQt5.QtCore import QThread, pyqtSignal

class SessionWorker(QThread):
    """Worker thread to run session processing in the background"""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, session_manager, before_path, after_path):
        super().__init__()
        self.session_manager = session_manager
        self.before_path = before_path
        self.after_path = after_path

    def run(self):
        try:
            self.session_manager.start_session(self.before_path, self.after_path)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class ReportWorker(QThread):
    """Worker thread to generate PDF report in the background"""
    finished = pyqtSignal(str)  # Emits the output path on success
    error = pyqtSignal(str)

    def __init__(self, session_manager, generate_report_func):
        super().__init__()
        self.session_manager = session_manager
        self.generate_report_func = generate_report_func

    def run(self):
        try:
            output_path = self.generate_report_func(self.session_manager)
            self.finished.emit(output_path)
        except Exception as e:
            self.error.emit(str(e))