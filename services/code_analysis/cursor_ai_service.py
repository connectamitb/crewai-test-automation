import os
import logging
import paramiko
from typing import Dict, Any

class CursorAIService:
    """Service for interacting with Cursor AI's code analysis features via SSH"""

    def __init__(self):
        self.ssh_host = "ssh.cursor.sh"  # Replace with actual Cursor AI SSH host
        self.ssh_port = 22
        self.logger = logging.getLogger(__name__)
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def _connect(self):
        """Establish SSH connection to Cursor AI"""
        try:
            self.ssh_client.connect(
                hostname=self.ssh_host,
                port=self.ssh_port,
                username=os.environ.get('CURSOR_SSH_USER'),
                key_filename=os.environ.get('CURSOR_SSH_KEY_PATH')
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to Cursor AI via SSH: {str(e)}")
            raise

    def analyze_code(self, code: str) -> Dict[Any, Any]:
        """
        Analyze the given code using Cursor AI via SSH

        Args:
            code (str): The code to analyze

        Returns:
            Dict: Analysis results from Cursor AI
        """
        try:
            self._connect()
            stdin, stdout, stderr = self.ssh_client.exec_command(f'analyze "{code}"')
            result = stdout.read().decode()
            error = stderr.read().decode()

            if error:
                raise Exception(f"Error from Cursor AI: {error}")

            return {"analysis": result}

        except Exception as e:
            self.logger.error(f"Error analyzing code with Cursor AI: {str(e)}")
            raise
        finally:
            self.ssh_client.close()