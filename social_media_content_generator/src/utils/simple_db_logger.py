import os
import uuid
import time
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

class SimpleDatabaseLogger:
    def __init__(self, logger: logging.Logger):
        """Initialize the simple database logger with direct HTTP requests."""
        self.logger = logger
        load_dotenv()
        
        # Initialize Supabase connection
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            self.logger.error("Supabase credentials not found in environment variables")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        
        # Set up headers for Supabase API
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        self.logger.info("Simple database logger initialized successfully")
        
        # Track current session
        self.current_session_id = None
        self.current_session_uuid = None
        self.user_id = os.getenv('USER_ID', 'default_user')
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make a request to Supabase API."""
        url = f"{self.supabase_url}/rest/v1/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except Exception as e:
            self.logger.error(f"API request failed: {str(e)}")
            raise
    
    def start_generation_session(self, idea: str, platform: str, tones: List[str] = None, 
                               audiences: List[str] = None, user_id: str = None) -> str:
        """Start a new generation session and return the session ID."""
        try:
            session_id = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id or self.user_id,
                'original_idea': idea,
                'target_platform': platform,
                'requested_tones': tones or [],
                'requested_audiences': audiences or [],
                'status': 'started',
                'start_time': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self._make_request('POST', 'generation_sessions', session_data)
            
            if result:
                self.current_session_id = session_id
                self.current_session_uuid = result[0]['id'] if isinstance(result, list) else result['id']
                self.logger.info(f"Started generation session: {session_id}")
                return session_id
            else:
                raise Exception("Failed to create session record")
                
        except Exception as e:
            self.logger.error(f"Failed to start generation session: {str(e)}")
            # Don't raise - continue without database logging
            return None
    
    def log_agent_execution(self, agent_name: str, execution_order: int, 
                           input_data: Dict = None, output_data: Dict = None,
                           model_used: str = None, temperature: float = None,
                           tokens_used: int = 0, cost_usd: float = 0,
                           status: str = 'started', error_message: str = None) -> str:
        """Log an agent execution."""
        try:
            if not self.current_session_uuid:
                self.logger.warning("No active session. Skipping agent execution logging.")
                return None
            
            execution_data = {
                'session_id': self.current_session_uuid,
                'agent_name': agent_name,
                'execution_order': execution_order,
                'status': status,
                'input_data': input_data,
                'output_data': output_data,
                'tokens_used': tokens_used,
                'cost_usd': cost_usd,
                'model_used': model_used,
                'temperature': temperature,
                'start_time': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            if error_message:
                execution_data['error_message'] = error_message
            
            result = self._make_request('POST', 'agent_executions', execution_data)
            
            if result:
                execution_uuid = result[0]['id'] if isinstance(result, list) else result['id']
                self.logger.info(f"Logged {agent_name} execution (order {execution_order})")
                return execution_uuid
            else:
                raise Exception("Failed to create agent execution record")
                
        except Exception as e:
            self.logger.error(f"Failed to log agent execution: {str(e)}")
            return None
    
    def update_agent_execution(self, execution_uuid: str, status: str = 'completed',
                             output_data: Dict = None, tokens_used: int = None,
                             cost_usd: float = None, execution_time_ms: int = None,
                             error_message: str = None):
        """Update an agent execution with completion data."""
        try:
            update_data = {
                'status': status,
                'end_time': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            if output_data is not None:
                update_data['output_data'] = output_data
            if tokens_used is not None:
                update_data['tokens_used'] = tokens_used
            if cost_usd is not None:
                update_data['cost_usd'] = cost_usd
            if execution_time_ms is not None:
                update_data['execution_time_ms'] = execution_time_ms
            if error_message is not None:
                update_data['error_message'] = error_message
            
            self._make_request('PUT', f'agent_executions?id=eq.{execution_uuid}', update_data)
            self.logger.info(f"Updated agent execution {execution_uuid} with status: {status}")
            
        except Exception as e:
            self.logger.error(f"Failed to update agent execution: {str(e)}")
    
    def log_api_call(self, agent_execution_uuid: str, api_provider: str, endpoint: str,
                     model_used: str = None, request_data: Dict = None,
                     response_data: Dict = None, status_code: int = None,
                     tokens_used: int = 0, cost_usd: float = 0,
                     response_time_ms: int = None, error_message: str = None):
        """Log an API call."""
        try:
            api_call_data = {
                'session_id': self.current_session_uuid,
                'agent_execution_id': agent_execution_uuid,
                'api_provider': api_provider,
                'endpoint': endpoint,
                'model_used': model_used,
                'request_data': request_data,
                'response_data': response_data,
                'status_code': status_code,
                'tokens_used': tokens_used,
                'cost_usd': cost_usd,
                'response_time_ms': response_time_ms,
                'created_at': datetime.now().isoformat()
            }
            
            if error_message:
                api_call_data['error_message'] = error_message
            
            self._make_request('POST', 'api_calls', api_call_data)
            self.logger.info(f"Logged API call to {api_provider} {endpoint}")
            
        except Exception as e:
            self.logger.error(f"Failed to log API call: {str(e)}")
    
    def log_image_generation(self, agent_execution_uuid: str, prompt: str,
                           generated_image_url: str = None, image_size: str = None,
                           model_used: str = None, cost_usd: float = 0,
                           status: str = 'started', error_message: str = None):
        """Log an image generation."""
        try:
            image_data = {
                'session_id': self.current_session_uuid,
                'agent_execution_id': agent_execution_uuid,
                'prompt': prompt,
                'generated_image_url': generated_image_url,
                'image_size': image_size,
                'model_used': model_used,
                'status': status,
                'cost_usd': cost_usd,
                'created_at': datetime.now().isoformat()
            }
            
            if error_message:
                image_data['error_message'] = error_message
            
            self._make_request('POST', 'image_generations', image_data)
            self.logger.info(f"Logged image generation with status: {status}")
            
        except Exception as e:
            self.logger.error(f"Failed to log image generation: {str(e)}")
    
    def log_error(self, agent_execution_uuid: str = None, error_type: str = 'general',
                  error_message: str = None, stack_trace: str = None,
                  context_data: Dict = None, severity: str = 'error'):
        """Log an error."""
        try:
            error_data = {
                'session_id': self.current_session_uuid,
                'error_type': error_type,
                'error_message': error_message or 'Unknown error',
                'stack_trace': stack_trace,
                'context_data': context_data,
                'severity': severity,
                'created_at': datetime.now().isoformat()
            }
            
            if agent_execution_uuid:
                error_data['agent_execution_id'] = agent_execution_uuid
            
            self._make_request('POST', 'error_logs', error_data)
            self.logger.error(f"Logged error: {error_type} - {error_message}")
            
        except Exception as e:
            self.logger.error(f"Failed to log error: {str(e)}")
    
    def log_user_facing_error(self, error_type: str, error_category: str, 
                             error_message: str, request_id: str = None,
                             session_id: str = None):
        """
        Log only user-facing errors to the error_logs table.
        
        Args:
            error_type: Type of error (e.g., "generation_error", "APIError", "AuthError")
            error_category: Category of error (e.g., "social_content", "image", "video")
            error_message: The exact error message shown to the user
            request_id: UUID for current request (optional)
            session_id: UUID from current user session (optional)
        """
        try:
            # Generate error_id (UUID)
            error_id = str(uuid.uuid4())
            
            # Use provided session_id or current session
            current_session = session_id or self.current_session_id
            
            error_data = {
                'error_id': error_id,
                'request_id': request_id or str(uuid.uuid4()),
                'session_id': current_session,
                'error_type': error_type,
                'error_category': error_category,
                'error_message': error_message,
                'timestamp': datetime.now().isoformat()
            }
            
            self._make_request('POST', 'error_logs', error_data)
            self.logger.info(f"Logged user-facing error: {error_type} - {error_category} - {error_message}")
            
        except Exception as e:
            self.logger.error(f"Failed to log user-facing error: {str(e)}")
    
    def log_performance_metric(self, metric_name: str, metric_value: float,
                             metric_unit: str = None):
        """Log a performance metric."""
        try:
            metric_data = {
                'session_id': self.current_session_uuid,
                'metric_name': metric_name,
                'metric_value': metric_value,
                'metric_unit': metric_unit,
                'created_at': datetime.now().isoformat()
            }
            
            self._make_request('POST', 'performance_metrics', metric_data)
            self.logger.info(f"Logged performance metric: {metric_name} = {metric_value} {metric_unit}")
            
        except Exception as e:
            self.logger.error(f"Failed to log performance metric: {str(e)}")
    
    def complete_generation_session(self, status: str = 'completed', 
                                 total_tokens_used: int = 0, total_cost_usd: float = 0,
                                 error_message: str = None):
        """Complete the current generation session."""
        try:
            if not self.current_session_uuid:
                self.logger.warning("No active session to complete.")
                return
            
            update_data = {
                'status': status,
                'end_time': datetime.now().isoformat(),
                'total_tokens_used': total_tokens_used,
                'total_cost_usd': total_cost_usd,
                'updated_at': datetime.now().isoformat()
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            self._make_request('PUT', f'generation_sessions?id=eq.{self.current_session_uuid}', update_data)
            self.logger.info(f"Completed generation session with status: {status}")
            
            # Reset session tracking
            self.current_session_id = None
            self.current_session_uuid = None
            
        except Exception as e:
            self.logger.error(f"Failed to complete generation session: {str(e)}") 