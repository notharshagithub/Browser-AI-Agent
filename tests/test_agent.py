import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Put root dir in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import WebsiteAutomationAgent

class TestAgent(unittest.TestCase):
    
    @patch('agent.agent.PlaywrightBrowserManager')
    @patch('agent.agent.LLMClient')
    def test_agent_initialization(self, mock_llm_client, mock_browser_mgr):
        """Test agent initializes state variables correctly."""
        agent = WebsiteAutomationAgent()
        self.assertFalse(agent.session_active)
        self.assertEqual(agent.step_count, 0)
        self.assertIsNone(agent.last_failure_reason)
        self.assertIsNone(agent.success_summary)
        
    @patch('agent.agent.PlaywrightBrowserManager')
    @patch('agent.agent.LLMClient')
    def test_agent_session_management(self, mock_llm_client, mock_browser_mgr):
        """Test start_session and close_session flags update correctly."""
        # Setup mocks
        mock_browser_instance = MagicMock()
        mock_browser_instance.open_browser.return_value = {"success": True}
        mock_browser_mgr.return_value = mock_browser_instance
        
        agent = WebsiteAutomationAgent()
        
        # Test start
        self.assertTrue(agent.start_session(headless=True))
        self.assertTrue(agent.session_active)
        
        # Test close
        agent.close_session()
        self.assertFalse(agent.session_active)
        mock_browser_instance.close_browser.assert_called_once()

    @patch('agent.agent.PlaywrightBrowserManager')
    @patch('agent.agent.LLMClient')
    def test_agent_run_task_fails_when_browser_fails(self, mock_llm_client, mock_browser_mgr):
        """Verify run_task records browser failure reasons when start_session fails."""
        mock_browser_instance = MagicMock()
        # Mock is_session_healthy to return False and start_session to fail
        mock_browser_instance.open_browser.return_value = {"success": False, "message": "Failed to launch"}
        mock_browser_mgr.return_value = mock_browser_instance
        
        agent = WebsiteAutomationAgent()
        agent.browser_manager.page = None
        
        # Run task
        success = agent.run_task("Search for playwright", max_steps=3)
        self.assertFalse(success)
        self.assertIn("Could not initialize or launch browser context", agent.last_failure_reason)

if __name__ == '__main__':
    unittest.main()
