import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch

# We need to patch the tkinterdnd2 import as it's not available in the environment
# and also other environment dependencies like OpenAI
with patch.dict('sys.modules', {'tkinterdnd2': MagicMock(), 'openai': MagicMock(), 'winsound': MagicMock()}):
    from IMTB-D_ui import App

class TestUIPauseButton(unittest.TestCase):

    def test_pause_button_reset(self):
        """
        Tests that the Pause button text is reset when a new file transfer starts.
        """
        # Patch dependencies that are not available in the test environment
        with patch('IMTB-D_ui.load_dotenv'), \
             patch('IMTB-D_ui.OpenAI'), \
             patch('IMTB-D_ui.requests.post'), \
             patch('IMTB-D_ui.subprocess.Popen'), \
             patch('IMTB-D_ui.Tailer'), \
             patch('IMTB-D_ui.JSONL_PATH.exists', return_value=True), \
             patch('IMTB-D_ui.ROUTES_PATH.exists', return_value=True), \
             patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='[]'), \
             patch('IMTB-D_ui.Path.exists', return_value=True):

            # 1. Create the app instance
            # We need a root window for the App, but we don't want to actually show it.
            # We can use a real Tk root and then withdraw it.
            root = tk.Tk()
            root.withdraw()
            app = App()

            # 2. Simulate a click on the "Pause" button
            # This should change the button text to "Resume"
            app.btn_ft_pause.invoke()
            self.assertEqual(app.btn_ft_pause.cget("text"), "Resume")

            # 3. Call the _ft_start_worker method
            # This simulates starting a new file transfer
            app._ft_start_worker(paths=[])

            # 4. Check that the button text is now "Pause"
            # This is the core of the fix. Before the fix, the text would remain "Resume".
            self.assertEqual(app.btn_ft_pause.cget("text"), "Pause")

            # Clean up the app window
            app.destroy()

if __name__ == '__main__':
    # This test cannot be run directly in this environment due to Tkinter dependency.
    # However, it demonstrates the logic for verifying the fix.
    # To run this test, you would need a graphical environment with Tkinter installed.
    print("This test file is intended to demonstrate the verification logic.")
    print("It cannot be run in this environment.")
    # unittest.main()
