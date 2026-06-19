import unittest
import sys
import os
from io import StringIO
from unittest.mock import patch

# Put root dir in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent.theme as theme

class TestTheme(unittest.TestCase):
    
    def test_theme_colors(self):
        """Verify cyberpunk theme colors are defined as non-empty strings."""
        self.assertTrue(len(theme.CYAN) > 0)
        self.assertTrue(len(theme.GREEN) > 0)
        self.assertTrue(len(theme.RESET) > 0)

    def test_set_theme(self):
        """Verify set_theme switches CURRENT_THEME and modifies color variables."""
        theme.set_theme("retro")
        self.assertEqual(theme.CURRENT_THEME, "retro")
        self.assertEqual(theme.CYAN, theme.THEMES["retro"]["CYAN"])
        
        # Reset back to cyberpunk
        theme.set_theme("cyberpunk")
        self.assertEqual(theme.CURRENT_THEME, "cyberpunk")

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_horizontal_divider(self, mock_stdout):
        """Test the horizontal divider output formatting."""
        theme.print_horizontal_divider(theme.SINGLE_LINE)
        output = mock_stdout.getvalue()
        self.assertIn(theme.SINGLE_LINE, output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_welcome_banner(self, mock_stdout):
        """Test welcome banner contents are correctly rendered with header flags."""
        theme.print_welcome_banner()
        output = mock_stdout.getvalue()
        self.assertIn("B R O W S E R", output)
        self.assertIn("A U T O M A T I O N", output)
        self.assertIn("⚡ BrowseIQ UI Console", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_status_card(self, mock_stdout):
        """Test status connection cards contain URLs and indicators."""
        theme.print_status_card("TEST TITLE", "https://example.com", "CONNECTED")
        output = mock_stdout.getvalue()
        self.assertIn("TEST TITLE", output)
        self.assertIn("https://example.com", output)
        self.assertIn("CONNECTED", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_step_header(self, mock_stdout):
        """Test visual step tracking header outputs correctly."""
        theme.print_step_header(2, 5, 12)
        output = mock_stdout.getvalue()
        self.assertIn("COGNITIVE STEP [2/5]", output)
        self.assertIn("Global: 12", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_failure_card(self, mock_stdout):
        """Test diagnostic error diagnostics logs out failure causes."""
        theme.print_failure_card("Selector not found", 4)
        output = mock_stdout.getvalue()
        self.assertIn("FAILURE DIAGNOSTICS", output)
        self.assertIn("Failure Reason: Selector not found", output)
        self.assertIn("Steps executed: 4", output)

if __name__ == '__main__':
    unittest.main()
