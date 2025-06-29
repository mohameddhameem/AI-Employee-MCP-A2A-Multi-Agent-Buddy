#!/usr/bin/env python3
"""
Phase 6: Agent-to-Agent (A2A) Communication Protocol
Standardized protocol for secure, efficient agent communication
"""

import json
import time
import uuid
import hashlib
import hmac
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import requests

class MessageType(Enum):
    """Standard A2A message types"""
    DISCOVERY_REQUEST = "discovery_request"
    DISCOVERY_RESPONSE = "discovery_response"
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    CAPABILITY_QUERY = "capability_query"
    CAPABILITY_RESPONSE = "capability_response"
    HEALTH_CHECK = "health_check"
    HEALTH_RESPONSE = "health_response"
    DELEGATION_REQUEST = "delegation_request"
    DELEGATION_RESPONSE = "delegation_response"
    COORDINATION_MESSAGE = "coordination_message"

@dataclass
class A2AMessage:
    """Standard A2A message format"""
    message_id: str
    message_type: MessageType
    sender_id: str
    recipient_id: str
    timestamp: float
    payload: Dict[str, Any]
    signature: Optional[str] = None
    correlation_id: Optional[str] = None  # For request-response tracking
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create from dictionary"""
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)

@dataclass
class AgentCapability:
    """Agent capability description"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    keywords: List[str]
    confidence_level: float  # 0.0 to 1.0

@dataclass
class AgentProfile:
    """Agent profile for discovery and coordination"""
    agent_id: str
    agent_name: str
    agent_type: str
    version: str
    endpoint: str
    capabilities: List[AgentCapability]
    specializations: List[str]
    trust_level: str = "basic"  # basic, verified, trusted
    last_seen: float = 0.0

class A2AProtocol:
    """Agent-to-Agent communication protocol implementation"""
    
    def __init__(self, agent_id: str, agent_name: str, endpoint: str, secret_key: Optional[str] = None):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.endpoint = endpoint
        self.secret_key = secret_key or "default_a2a_key"
        
        # Agent registry for discovered agents
        self.known_agents: Dict[str, AgentProfile] = {}
        
        # Message tracking
        self.pending_requests: Dict[str, float] = {}  # correlation_id -> timestamp
        self.request_timeout = 30.0  # seconds
    
    def create_message(self, 
                      message_type: MessageType, 
                      recipient_id: str, 
                      payload: Dict[str, Any],
                      correlation_id: Optional[str] = None) -> A2AMessage:
        """Create a standardized A2A message"""
        
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            timestamp=time.time(),
            payload=payload,
            correlation_id=correlation_id
        )
        
        # Sign the message for security
        if self.secret_key:
            message.signature = self._sign_message(message)
        
        return message
    
    def _sign_message(self, message: A2AMessage) -> str:
        """Create HMAC signature for message authentication"""
        # Create signature payload (exclude signature field)
        sign_data = {
            "message_id": message.message_id,
            "message_type": message.message_type.value,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "timestamp": message.timestamp,
            "payload": message.payload
        }
        
        message_bytes = json.dumps(sign_data, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message_bytes,
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_message(self, message: A2AMessage) -> bool:
        """Verify message signature"""
        if not message.signature or not self.secret_key:
            return True  # Skip verification if no signature/key
        
        expected_signature = self._sign_message(message)
        return hmac.compare_digest(message.signature, expected_signature)
    
    def send_message(self, message: A2AMessage, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """Send message to another agent via HTTP"""
        
        # Find recipient endpoint
        recipient_endpoint = None
        if message.recipient_id in self.known_agents:
            recipient_endpoint = self.known_agents[message.recipient_id].endpoint
        else:
            # Try common endpoint pattern
            recipient_endpoint = f"http://localhost:800{len(self.known_agents) + 2}"
        
        if not recipient_endpoint:
            raise ValueError(f"Unknown recipient: {message.recipient_id}")
        
        try:
            # Track pending requests
            if message.correlation_id:
                self.pending_requests[message.correlation_id] = time.time()
            
            # Send HTTP POST to agent's A2A endpoint
            response = requests.post(
                f"{recipient_endpoint}/a2a",
                json=message.to_dict(),
                headers={
                    "Content-Type": "application/json",
                    "X-A2A-Protocol": "1.0",
                    "X-Sender-ID": self.agent_id
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "details": response.text}
                
        except requests.exceptions.ConnectionError:
            return {"error": "connection_refused", "endpoint": recipient_endpoint}
        except Exception as e:
            return {"error": "send_failed", "details": str(e)}
    
    def discover_agents(self, broadcast_endpoints: List[str]) -> List[AgentProfile]:
        """Discover other agents in the network"""
        discovered = []
        
        discovery_message = self.create_message(
            MessageType.DISCOVERY_REQUEST,
            "broadcast",
            {
                "requesting_agent": {
                    "id": self.agent_id,
                    "name": self.agent_name,
                    "endpoint": self.endpoint
                },
                "discovery_timestamp": time.time()
            }
        )
        
        for endpoint in broadcast_endpoints:
            try:
                response = requests.post(
                    f"{endpoint}/a2a",
                    json=discovery_message.to_dict(),
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("message_type") == MessageType.DISCOVERY_RESPONSE.value:
                        agent_info = data.get("payload", {}).get("agent_profile")
                        if agent_info:
                            profile = AgentProfile(**agent_info)
                            profile.last_seen = time.time()
                            self.known_agents[profile.agent_id] = profile
                            discovered.append(profile)
                            
            except Exception as e:
                print(f"Discovery failed for {endpoint}: {e}")
        
        return discovered
    
    def delegate_task(self, recipient_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Delegate a task to another agent using A2A protocol"""
        
        correlation_id = str(uuid.uuid4())
        
        delegation_message = self.create_message(
            MessageType.DELEGATION_REQUEST,
            recipient_id,
            {
                "task": task,
                "context": context or {},
                "delegation_timestamp": time.time(),
                "priority": "normal",
                "timeout": 30.0
            },
            correlation_id=correlation_id
        )
        
        result = self.send_message(delegation_message)
        
        # Clean up tracking
        if correlation_id in self.pending_requests:
            del self.pending_requests[correlation_id]
        
        return result or {"error": "no_response"}
    
    def query_capabilities(self, recipient_id: str) -> Dict[str, Any]:
        """Query another agent's capabilities"""
        
        capability_message = self.create_message(
            MessageType.CAPABILITY_QUERY,
            recipient_id,
            {
                "requesting_capabilities": True,
                "query_timestamp": time.time()
            }
        )
        
        return self.send_message(capability_message) or {"error": "no_response"}
    
    def health_check_agent(self, recipient_id: str) -> Dict[str, Any]:
        """Check health of another agent via A2A protocol"""
        
        health_message = self.create_message(
            MessageType.HEALTH_CHECK,
            recipient_id,
            {
                "health_check": True,
                "timestamp": time.time()
            }
        )
        
        return self.send_message(health_message) or {"error": "no_response"}
    
    def handle_incoming_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming A2A message"""
        
        try:
            message = A2AMessage.from_dict(message_data)
            
            # Verify message signature
            if not self.verify_message(message):
                return {
                    "error": "invalid_signature",
                    "message": "Message signature verification failed"
                }
            
            # Route message based on type
            handler_map = {
                MessageType.DISCOVERY_REQUEST: self._handle_discovery_request,
                MessageType.CAPABILITY_QUERY: self._handle_capability_query,
                MessageType.HEALTH_CHECK: self._handle_health_check,
                MessageType.DELEGATION_REQUEST: self._handle_delegation_request,
                MessageType.TASK_REQUEST: self._handle_task_request,
            }
            
            handler = handler_map.get(message.message_type)
            if handler:
                return handler(message)
            else:
                return {
                    "error": "unsupported_message_type",
                    "message_type": message.message_type.value
                }
                
        except Exception as e:
            return {
                "error": "message_processing_failed",
                "details": str(e)
            }
    
    def _handle_discovery_request(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle agent discovery request"""
        
        # Create agent profile response
        agent_profile = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": "specialized",
            "version": "1.0",
            "endpoint": self.endpoint,
            "capabilities": [],  # To be populated by specific agents
            "specializations": [],  # To be populated by specific agents
            "trust_level": "basic",
            "last_seen": time.time()
        }
        
        response = self.create_message(
            MessageType.DISCOVERY_RESPONSE,
            message.sender_id,
            {"agent_profile": agent_profile},
            correlation_id=message.correlation_id
        )
        
        return response.to_dict()
    
    def _handle_capability_query(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle capability query"""
        
        # Base capabilities - to be extended by specific agents
        capabilities = [
            {
                "name": "basic_communication",
                "description": "Basic A2A protocol communication",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
                "keywords": ["communication", "protocol"],
                "confidence_level": 1.0
            }
        ]
        
        response = self.create_message(
            MessageType.CAPABILITY_RESPONSE,
            message.sender_id,
            {"capabilities": capabilities},
            correlation_id=message.correlation_id
        )
        
        return response.to_dict()
    
    def _handle_health_check(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle health check request"""
        
        health_status = {
            "status": "healthy",
            "agent_id": self.agent_id,
            "timestamp": time.time(),
            "uptime": time.time(),  # Simplified
            "capabilities_count": 1,
            "known_agents_count": len(self.known_agents)
        }
        
        response = self.create_message(
            MessageType.HEALTH_RESPONSE,
            message.sender_id,
            health_status,
            correlation_id=message.correlation_id
        )
        
        return response.to_dict()
    
    def _handle_delegation_request(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle task delegation request - to be overridden by specific agents"""
        
        response = self.create_message(
            MessageType.DELEGATION_RESPONSE,
            message.sender_id,
            {
                "status": "not_implemented",
                "message": "Task delegation not implemented in base A2A protocol"
            },
            correlation_id=message.correlation_id
        )
        
        return response.to_dict()
    
    def _handle_task_request(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle direct task request - to be overridden by specific agents"""
        
        response = self.create_message(
            MessageType.TASK_RESPONSE,
            message.sender_id,
            {
                "status": "not_implemented", 
                "message": "Task processing not implemented in base A2A protocol"
            },
            correlation_id=message.correlation_id
        )
        
        return response.to_dict()
    
    def cleanup_expired_requests(self):
        """Clean up expired pending requests"""
        current_time = time.time()
        expired_keys = [
            corr_id for corr_id, timestamp in self.pending_requests.items()
            if current_time - timestamp > self.request_timeout
        ]
        
        for key in expired_keys:
            del self.pending_requests[key]
    
    def get_protocol_status(self) -> Dict[str, Any]:
        """Get A2A protocol status information"""
        return {
            "protocol_version": "1.0",
            "agent_id": self.agent_id,
            "known_agents": len(self.known_agents),
            "pending_requests": len(self.pending_requests),
            "security_enabled": bool(self.secret_key),
            "supported_message_types": [mt.value for mt in MessageType],
            "agent_registry": {
                agent_id: {
                    "name": profile.agent_name,
                    "type": profile.agent_type,
                    "endpoint": profile.endpoint,
                    "last_seen": profile.last_seen,
                    "capabilities_count": len(profile.capabilities)
                }
                for agent_id, profile in self.known_agents.items()
            }
        }
