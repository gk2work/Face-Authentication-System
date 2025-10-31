"""WebSocket API endpoints for real-time updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from typing import Optional
import asyncio
import json

from app.services.websocket_manager import websocket_manager
from app.services.auth_service import auth_service
from app.core.logging import logger
from app.utils.error_responses import ErrorCode, create_error_response

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time updates.
    
    This endpoint provides:
    - Real-time application processing updates
    - Progress notifications during face detection and embedding
    - Completion and error notifications
    - Automatic reconnection support
    
    **Connection Flow:**
    1. Client connects with unique client_id
    2. Optional JWT token authentication
    3. Connection established and confirmed
    4. Client subscribes to application updates
    5. Server sends updates as processing occurs
    6. Connection maintained with periodic pings
    
    **Message Types:**
    - `connection_established`: Sent when connection is successful
    - `processing_update`: Sent during application processing
    - `processing_complete`: Sent when processing finishes
    - `processing_error`: Sent if processing fails
    - `ping`: Periodic keep-alive message
    
    **Client Messages:**
    - `subscribe`: Subscribe to application updates
      ```json
      {
        "action": "subscribe",
        "application_id": "app-123"
      }
      ```
    
    - `unsubscribe`: Unsubscribe from application updates
      ```json
      {
        "action": "unsubscribe",
        "application_id": "app-123"
      }
      ```
    
    - `pong`: Response to ping (optional)
      ```json
      {
        "action": "pong"
      }
      ```
    
    **Server Messages:**
    
    Connection Established:
    ```json
    {
      "type": "connection_established",
      "client_id": "client-123",
      "timestamp": "2024-01-01T00:00:00.000Z",
      "message": "WebSocket connection established successfully"
    }
    ```
    
    Processing Update:
    ```json
    {
      "type": "processing_update",
      "application_id": "app-123",
      "stage": "face_detection",
      "status": "in_progress",
      "progress": 50,
      "message": "Detecting face in photograph",
      "timestamp": "2024-01-01T00:00:00.000Z"
    }
    ```
    
    Processing Complete:
    ```json
    {
      "type": "processing_complete",
      "application_id": "app-123",
      "result": {
        "status": "approved",
        "identity_id": "id-456",
        "is_duplicate": false
      },
      "timestamp": "2024-01-01T00:00:00.000Z"
    }
    ```
    
    Processing Error:
    ```json
    {
      "type": "processing_error",
      "application_id": "app-123",
      "error_code": "E001",
      "error_message": "No face detected",
      "timestamp": "2024-01-01T00:00:00.000Z"
    }
    ```
    
    **Authentication:**
    - Optional JWT token via query parameter
    - If provided, token is validated before connection
    - Unauthenticated connections are allowed but may have limited access
    
    **Error Handling:**
    - Connection errors are logged and connection is closed
    - Invalid messages are logged but don't close connection
    - Automatic cleanup on disconnect
    
    Args:
        websocket: WebSocket connection instance
        client_id: Unique identifier for the client
        token: Optional JWT authentication token
    """
    # Optional authentication
    user_id = None
    if token:
        try:
            token_data = auth_service.decode_access_token(token)
            if token_data:
                user_id = token_data.username
                logger.info(f"WebSocket authenticated for user: {user_id}")
            else:
                logger.warning("WebSocket authentication failed: invalid token")
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {str(e)}")
            # Allow connection but mark as unauthenticated
            user_id = None
    
    # Prepare metadata
    metadata = {
        "user_id": user_id,
        "authenticated": user_id is not None,
        "client_host": websocket.client.host if websocket.client else None
    }
    
    try:
        # Connect the WebSocket
        await websocket_manager.connect(websocket, client_id, metadata)
        
        # Start message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    action = message.get("action")
                    
                    if action == "subscribe":
                        # Subscribe to application updates
                        application_id = message.get("application_id")
                        if application_id:
                            websocket_manager.subscribe_to_application(client_id, application_id)
                            
                            # Send confirmation
                            await websocket_manager.send_personal_message(
                                client_id=client_id,
                                message={
                                    "type": "subscription_confirmed",
                                    "application_id": application_id,
                                    "message": f"Subscribed to updates for application {application_id}"
                                }
                            )
                        else:
                            logger.warning(f"Subscribe action missing application_id from {client_id}")
                    
                    elif action == "unsubscribe":
                        # Unsubscribe from application updates
                        application_id = message.get("application_id")
                        if application_id:
                            websocket_manager.unsubscribe_from_application(client_id, application_id)
                            
                            # Send confirmation
                            await websocket_manager.send_personal_message(
                                client_id=client_id,
                                message={
                                    "type": "unsubscription_confirmed",
                                    "application_id": application_id,
                                    "message": f"Unsubscribed from updates for application {application_id}"
                                }
                            )
                        else:
                            logger.warning(f"Unsubscribe action missing application_id from {client_id}")
                    
                    elif action == "pong":
                        # Client responded to ping
                        logger.debug(f"Received pong from {client_id}")
                    
                    elif action == "get_stats":
                        # Send connection statistics (admin only)
                        if user_id:  # Only for authenticated users
                            stats = websocket_manager.get_stats()
                            await websocket_manager.send_personal_message(
                                client_id=client_id,
                                message={
                                    "type": "stats",
                                    "data": stats
                                }
                            )
                    
                    else:
                        logger.warning(f"Unknown action '{action}' from {client_id}")
                        await websocket_manager.send_personal_message(
                            client_id=client_id,
                            message={
                                "type": "error",
                                "message": f"Unknown action: {action}"
                            }
                        )
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {client_id}: {data}")
                    await websocket_manager.send_personal_message(
                        client_id=client_id,
                        message={
                            "type": "error",
                            "message": "Invalid JSON format"
                        }
                    )
            
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {client_id}")
                break
            
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {str(e)}")
                # Don't break the loop for non-critical errors
                await asyncio.sleep(0.1)
    
    except Exception as e:
        logger.error(f"WebSocket connection error for {client_id}: {str(e)}")
    
    finally:
        # Clean up connection
        websocket_manager.disconnect(client_id)


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns information about:
    - Number of active connections
    - Number of active subscriptions
    - Total subscribers across all applications
    - List of connected client IDs
    
    This endpoint is useful for monitoring and debugging.
    
    Returns:
        Dictionary with connection statistics
    """
    stats = websocket_manager.get_stats()
    return {
        "status": "success",
        "stats": stats
    }
