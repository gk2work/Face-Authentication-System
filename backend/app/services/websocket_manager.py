"""WebSocket connection manager for real-time updates"""

from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio

from app.core.logging import logger


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Features:
    - Connection lifecycle management (connect, disconnect)
    - Broadcasting to all clients
    - Targeted messages to specific clients
    - Connection state tracking
    - Automatic cleanup on disconnect
    - Error handling and reconnection support
    """
    
    def __init__(self):
        # Active connections: client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Application subscriptions: application_id -> Set[client_id]
        self.application_subscriptions: Dict[str, Set[str]] = {}
        
        # Client metadata: client_id -> metadata
        self.client_metadata: Dict[str, Dict[str, Any]] = {}
        
        logger.info("WebSocket connection manager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection instance
            client_id: Unique identifier for the client
            metadata: Optional metadata about the client (user_id, ip, etc.)
        """
        try:
            await websocket.accept()
            
            # Store connection
            self.active_connections[client_id] = websocket
            
            # Store metadata
            self.client_metadata[client_id] = metadata or {}
            self.client_metadata[client_id]["connected_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"WebSocket connected: {client_id} (Total connections: {len(self.active_connections)})")
            
            # Send connection confirmation
            await self.send_personal_message(
                client_id=client_id,
                message={
                    "type": "connection_established",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "WebSocket connection established successfully"
                }
            )
            
        except Exception as e:
            logger.error(f"Error connecting WebSocket for {client_id}: {str(e)}")
            raise
    
    def disconnect(self, client_id: str):
        """
        Remove a WebSocket connection and clean up subscriptions.
        
        Args:
            client_id: Unique identifier for the client
        """
        try:
            # Remove from active connections
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            
            # Remove from all application subscriptions
            for app_id in list(self.application_subscriptions.keys()):
                if client_id in self.application_subscriptions[app_id]:
                    self.application_subscriptions[app_id].remove(client_id)
                    
                # Clean up empty subscription sets
                if not self.application_subscriptions[app_id]:
                    del self.application_subscriptions[app_id]
            
            # Remove metadata
            if client_id in self.client_metadata:
                del self.client_metadata[client_id]
            
            logger.info(f"WebSocket disconnected: {client_id} (Remaining connections: {len(self.active_connections)})")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket for {client_id}: {str(e)}")
    
    async def send_personal_message(self, client_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific client.
        
        Args:
            client_id: Target client identifier
            message: Message data to send (will be JSON serialized)
        """
        if client_id not in self.active_connections:
            logger.warning(f"Cannot send message to {client_id}: not connected")
            return
        
        try:
            websocket = self.active_connections[client_id]
            
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()
            
            # Send as JSON
            await websocket.send_json(message)
            
            logger.debug(f"Sent message to {client_id}: {message.get('type', 'unknown')}")
            
        except WebSocketDisconnect:
            logger.warning(f"Client {client_id} disconnected while sending message")
            self.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error sending message to {client_id}: {str(e)}")
            self.disconnect(client_id)
    
    async def send_text_message(self, client_id: str, text: str):
        """
        Send a plain text message to a specific client.
        
        Args:
            client_id: Target client identifier
            text: Text message to send
        """
        if client_id not in self.active_connections:
            logger.warning(f"Cannot send text to {client_id}: not connected")
            return
        
        try:
            websocket = self.active_connections[client_id]
            await websocket.send_text(text)
            logger.debug(f"Sent text message to {client_id}")
        except Exception as e:
            logger.error(f"Error sending text to {client_id}: {str(e)}")
            self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message data to broadcast
            exclude: Optional set of client IDs to exclude from broadcast
        """
        exclude = exclude or set()
        
        # Add timestamp
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            if client_id in exclude:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {str(e)}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
        
        logger.debug(f"Broadcast message to {len(self.active_connections) - len(exclude)} clients")
    
    def subscribe_to_application(self, client_id: str, application_id: str):
        """
        Subscribe a client to updates for a specific application.
        
        Args:
            client_id: Client identifier
            application_id: Application identifier to subscribe to
        """
        if application_id not in self.application_subscriptions:
            self.application_subscriptions[application_id] = set()
        
        self.application_subscriptions[application_id].add(client_id)
        
        logger.info(f"Client {client_id} subscribed to application {application_id}")
    
    def unsubscribe_from_application(self, client_id: str, application_id: str):
        """
        Unsubscribe a client from application updates.
        
        Args:
            client_id: Client identifier
            application_id: Application identifier to unsubscribe from
        """
        if application_id in self.application_subscriptions:
            self.application_subscriptions[application_id].discard(client_id)
            
            # Clean up empty subscription sets
            if not self.application_subscriptions[application_id]:
                del self.application_subscriptions[application_id]
        
        logger.info(f"Client {client_id} unsubscribed from application {application_id}")
    
    async def send_application_update(self, application_id: str, update: Dict[str, Any]):
        """
        Send an update to all clients subscribed to an application.
        
        Args:
            application_id: Application identifier
            update: Update data to send
        """
        if application_id not in self.application_subscriptions:
            logger.debug(f"No subscribers for application {application_id}")
            return
        
        # Add application_id to update
        update["application_id"] = application_id
        
        # Add timestamp
        if "timestamp" not in update:
            update["timestamp"] = datetime.utcnow().isoformat()
        
        subscribers = self.application_subscriptions[application_id].copy()
        disconnected_clients = []
        
        for client_id in subscribers:
            if client_id not in self.active_connections:
                disconnected_clients.append(client_id)
                continue
            
            try:
                await self.send_personal_message(client_id, update)
            except Exception as e:
                logger.error(f"Error sending application update to {client_id}: {str(e)}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.unsubscribe_from_application(client_id, application_id)
            self.disconnect(client_id)
        
        logger.debug(f"Sent application update to {len(subscribers) - len(disconnected_clients)} subscribers")
    
    async def send_processing_update(
        self,
        application_id: str,
        stage: str,
        status: str,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Send a processing status update for an application.
        
        Args:
            application_id: Application identifier
            stage: Current processing stage (e.g., "face_detection", "embedding")
            status: Status of the stage (e.g., "in_progress", "completed", "failed")
            progress: Optional progress percentage (0-100)
            message: Optional status message
            details: Optional additional details
        """
        update = {
            "type": "processing_update",
            "stage": stage,
            "status": status,
            "progress": progress,
            "message": message,
            "details": details or {}
        }
        
        await self.send_application_update(application_id, update)
    
    async def send_completion_update(
        self,
        application_id: str,
        result: Dict[str, Any]
    ):
        """
        Send a completion update for an application.
        
        Args:
            application_id: Application identifier
            result: Processing result data
        """
        update = {
            "type": "processing_complete",
            "result": result
        }
        
        await self.send_application_update(application_id, update)
    
    async def send_error_update(
        self,
        application_id: str,
        error_code: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Send an error update for an application.
        
        Args:
            application_id: Application identifier
            error_code: Error code
            error_message: Error message
            details: Optional error details
        """
        update = {
            "type": "processing_error",
            "error_code": error_code,
            "error_message": error_message,
            "details": details or {}
        }
        
        await self.send_application_update(application_id, update)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_subscription_count(self, application_id: str) -> int:
        """Get the number of subscribers for an application."""
        return len(self.application_subscriptions.get(application_id, set()))
    
    def is_connected(self, client_id: str) -> bool:
        """Check if a client is connected."""
        return client_id in self.active_connections
    
    def get_client_metadata(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a client."""
        return self.client_metadata.get(client_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "active_connections": len(self.active_connections),
            "active_subscriptions": len(self.application_subscriptions),
            "total_subscribers": sum(len(subs) for subs in self.application_subscriptions.values()),
            "clients": list(self.active_connections.keys())
        }
    
    async def ping_all(self):
        """
        Send a ping to all connected clients to keep connections alive.
        This should be called periodically to prevent connection timeouts.
        """
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(ping_message)
            except Exception as e:
                logger.warning(f"Ping failed for {client_id}: {str(e)}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
        
        if disconnected_clients:
            logger.info(f"Cleaned up {len(disconnected_clients)} disconnected clients during ping")


# Global WebSocket manager instance
websocket_manager = ConnectionManager()
