# RTASPI dla Profesjonalnych Deweloperów

## Scenariusz: System wideokonferencji z przetwarzaniem audio/video w czasie rzeczywistym

Jako profesjonalny deweloper, otrzymałeś zadanie zbudowania niestandardowego systemu wideokonferencji, który powinien obsługiwać zaawansowane przetwarzanie strumieni audio i wideo, integrować się z istniejącym systemem autoryzacji i oferować wirtualną ścianę wideo dla wielu uczestników.

## Przewaga nad rozwiązaniami komercyjnymi

Komercyjne rozwiązania jak Zoom, Microsoft Teams czy WebEx:
- Pobierają wysokie opłaty licencyjne
- Oferują ograniczone API do integracji
- Nie dają pełnej kontroli nad przetwarzaniem multimediów
- Trudno je dostosować do specyficznych wymagań biznesowych

RTASPI pozwala stworzyć własne rozwiązanie, które:
- Ma niższe łączne koszty posiadania (TCO)
- Oferuje pełną kontrolę nad doświadczeniem użytkownika
- Może być dostosowane do konkretnych wymagań branżowych
- Integruje się bezproblemowo z istniejącą infrastrukturą

## Architektura systemu

Nasz system wideokonferencji składa się z trzech głównych komponentów:

1. **Serwer mediów** - zarządza strumieniami audio/wideo i sesją konferencji
2. **Back-end aplikacji** - odpowiada za autoryzację, składowanie danych i biznesową logikę
3. **Front-end aplikacji** - interfejs użytkownika dostępny przez przeglądarkę

### Diagram architektury

```
+------------------+        +-------------------+        +-------------------+
|                  |        |                   |        |                   |
|    Front-end     |<------>|     Back-end      |<------>|   Media Server    |
|    (Browser)     |   REST |     (Django)      |   APIs |     (RTASPI)      |
|                  |        |                   |        |                   |
+------------------+        +-------------------+        +-------------------+
                                     ^                          ^
                                     |                          |
                                     v                          v
                            +-------------------+       +-------------------+
                            |                   |       |                   |
                            |    Auth System    |       |   Storage System  |
                            |    (Existing)     |       |    (S3/Local)     |
                            |                   |       |                   |
                            +-------------------+       +-------------------+
```

## Implementacja serwera mediów z RTASPI

### 1. Konfiguracja i inicjalizacja

```python
# media_server.py

import os
import sys
import asyncio
import uuid
from datetime import datetime
from fastapi import FastAPI, WebSocket, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Set

from rtaspi.core import rtaspi
from rtaspi.streaming.webrtc import WebRTCServer, WebRTCSession
from rtaspi.processing.video.filters import VideoFilter
from rtaspi.processing.audio.filters import AudioFilter
from rtaspi.virtual_devices import VirtualDevice
from rtaspi.core.auth import JWTValidator

# Modele danych
class ConferenceRoom(BaseModel):
    room_id: str
    name: str
    owner_id: str
    participants: Set[str] = set()
    recording: bool = False
    recording_path: Optional[str] = None
    created_at: datetime = datetime.now()

class Participant(BaseModel):
    user_id: str
    name: str
    session_id: str
    room_id: str
    audio_enabled: bool = True
    video_enabled: bool = True
    joined_at: datetime = datetime.now()

# Konfiguracja RTASPI
config = {
    "system": {
        "storage_path": "/var/lib/conference-system/recordings",
        "log_level": "INFO"
    },
    "streaming": {
        "webrtc": {
            "port_start": 8088,
            "stun_server": "stun:stun.l.google.com:19302",
            "turn_server": os.environ.get("TURN_SERVER", ""),
            "turn_username": os.environ.get("TURN_USERNAME", ""),
            "turn_password": os.environ.get("TURN_PASSWORD", "")
        }
    },
    "virtual_devices": {
        "enable": True
    },
    "processing": {
        "video": {
            "background_removal": {
                "model": "mediapipe",
                "enable_gpu": True
            }
        },
        "audio": {
            "noise_reduction": {
                "enable": True,
                "strength": 0.7
            }
        }
    },
    "security": {
        "jwt": {
            "secret_key": os.environ.get("JWT_SECRET", ""),
            "algorithms": ["HS256"],
            "audience": "conference-system"
        }
    }
}

# Inicjalizacja
app_rtaspi = rtaspi(config=config)
webrtc_server = WebRTCServer(config=config["streaming"]["webrtc"])
jwt_validator = JWTValidator(config["security"]["jwt"])
api = FastAPI(title="Conference Media Server API")

# Stan aplikacji
active_rooms: Dict[str, ConferenceRoom] = {}
active_participants: Dict[str, Participant] = {}
webrtc_sessions: Dict[str, WebRTCSession] = {}

# Obsługa CORS
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dostosuj do swoich potrzeb
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Weryfikacja tokenu JWT
async def verify_token(token: str):
    try:
        payload = jwt_validator.validate(token)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Pomocnik do weryfikacji dostępu
async def verify_room_access(user_id: str, room_id: str):
    if room_id not in active_rooms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    room = active_rooms[room_id]
    if user_id != room.owner_id and user_id not in room.participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this room"
        )
    return room
```

### 2. Endpointy API dla zarządzania konferencjami

```python
# Endpoints dla obsługi pokojów konferencyjnych

@api.post("/rooms")
async def create_room(name: str, token: str):
    user = await verify_token(token)
    room_id = str(uuid.uuid4())
    new_room = ConferenceRoom(
        room_id=room_id,
        name=name,
        owner_id=user["sub"]
    )
    active_rooms[room_id] = new_room
    
    # Utwórz "wirtualny pokój" w RTASPI
    app_rtaspi.create_room(room_id, {"max_participants": 20})
    
    return {"room_id": room_id, "name": name}

@api.delete("/rooms/{room_id}")
async def delete_room(room_id: str, token: str):
    user = await verify_token(token)
    room = await verify_room_access(user["sub"], room_id)
    
    if user["sub"] != room.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the room owner can delete the room"
        )
    
    # Zakończ wszystkie sesje w pokoju
    for participant_id in room.participants:
        if participant_id in active_participants:
            session_id = active_participants[participant_id].session_id
            if session_id in webrtc_sessions:
                await webrtc_sessions[session_id].close()
                del webrtc_sessions[session_id]
            del active_participants[participant_id]
    
    # Usuń zasoby RTASPI
    app_rtaspi.delete_room(room_id)
    
    # Usuń pokój
    del active_rooms[room_id]
    
    return {"status": "success"}

@api.post("/rooms/{room_id}/join")
async def join_room(room_id: str, token: str):
    user = await verify_token(token)
    user_id = user["sub"]
    
    # Sprawdź czy pokój istnieje
    if room_id not in active_rooms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    room = active_rooms[room_id]
    
    # Dodaj uczestnika do pokoju
    room.participants.add(user_id)
    
    # Utwórz sesję dla nowego uczestnika
    session_id = str(uuid.uuid4())
    
    new_participant = Participant(
        user_id=user_id,
        name=user.get("name", "Anonymous"),
        session_id=session_id,
        room_id=room_id
    )
    
    active_participants[user_id] = new_participant
    
    # Utwórz sesję WebRTC
    webrtc_session = await webrtc_server.create_session(
        session_id=session_id, 
        room_id=room_id
    )
    webrtc_sessions[session_id] = webrtc_session
    
    return {
        "session_id": session_id,
        "room_id": room_id,
        "webrtc_config": webrtc_session.get_connection_config()
    }

@api.post("/rooms/{room_id}/leave")
async def leave_room(room_id: str, token: str):
    user = await verify_token(token)
    user_id = user["sub"]
    
    room = await verify_room_access(user_id, room_id)
    
    # Usuń uczestnika z pokoju
    if user_id in room.participants:
        room.participants.remove(user_id)
    
    # Zamknij sesję WebRTC
    if user_id in active_participants:
        session_id = active_participants[user_id].session_id
        if session_id in webrtc_sessions:
            await webrtc_sessions[session_id].close()
            del webrtc_sessions[session_id]
        del active_participants[user_id]
    
    return {"status": "success"}

@api.post("/rooms/{room_id}/start-recording")
async def start_recording(room_id: str, token: str):
    user = await verify_token(token)
    room = await verify_room_access(user["sub"], room_id)
    
    if room.recording:
        return {"status": "already_recording"}
    
    # Rozpocznij nagrywanie w RTASPI
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    recording_path = f"/var/lib/conference-system/recordings/{room_id}_{timestamp}"
    
    app_rtaspi.start_recording(
        room_id=room_id,
        output_path=recording_path,
        format="mp4",
        record_participants=True  # Nagrywaj wszystkich uczestników oddzielnie
    )
    
    room.recording = True
    room.recording_path = recording_path
    
    return {"status": "success", "recording_path": recording_path}

@api.post("/rooms/{room_id}/stop-recording")
async def stop_recording(room_id: str, token: str):
    user = await verify_token(token)
    room = await verify_room_access(user["sub"], room_id)
    
    if not room.recording:
        return {"status": "not_recording"}
    
    # Zatrzymaj nagrywanie
    app_rtaspi.stop_recording(room_id=room_id)
    
    room.recording = False
    recording_path = room.recording_path
    room.recording_path = None
    
    return {"status": "success", "recording_path": recording_path}
```

### 3. Obsługa WebSocket dla strumieni i sygnalizacji

```python
# Obsługa WebSocket dla komunikacji w czasie rzeczywistym

@api.websocket("/ws/conference/{session_id}")
async def websocket_conference(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    try:
        # Weryfikacja dostępu
        message = await websocket.receive_json()
        if "token" not in message:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        try:
            user = await verify_token(message["token"])
            user_id = user["sub"]
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Sprawdź czy użytkownik jest w pokoju
        if user_id not in active_participants:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        participant = active_participants[user_id]
        if participant.session_id != session_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Pobierz sesję WebRTC
        if session_id not in webrtc_sessions:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return
        
        webrtc_session = webrtc_sessions[session_id]
        
        # Połącz WebSocket z sesją WebRTC
        await webrtc_session.connect_signaling(websocket)
        
        # Obsługa komunikatów WebSocket
        async for message in websocket.iter_json():
            message_type = message.get("type")
            
            if message_type == "video_filter":
                # Stosowanie filtrów wideo
                filter_type = message.get("filter")
                filter_params = message.get("params", {})
                
                if filter_type == "background_blur":
                    await webrtc_session.apply_video_filter(
                        VideoFilter.BACKGROUND_BLUR,
                        {"strength": filter_params.get("strength", 0.5)}
                    )
                elif filter_type == "background_replacement":
                    await webrtc_session.apply_video_filter(
                        VideoFilter.BACKGROUND_REPLACEMENT,
                        {"image_path": filter_params.get("image_path")}
                    )
                elif filter_type == "noise_reduction":
                    await webrtc_session.apply_audio_filter(
                        AudioFilter.NOISE_REDUCTION,
                        {"strength": filter_params.get("strength", 0.7)}
                    )
                elif filter_type == "reset":
                    await webrtc_session.reset_filters()
            
            elif message_type == "mute_audio":
                # Wycisz audio
                participant.audio_enabled = False
                await webrtc_session.set_audio_enabled(False)
                
                # Powiadom innych uczestników
                await broadcast_participant_state(participant)
            
            elif message_type == "unmute_audio":
                # Włącz audio
                participant.audio_enabled = True
                await webrtc_session.set_audio_enabled(True)
                
                # Powiadom innych uczestników
                await broadcast_participant_state(participant)
            
            elif message_type == "disable_video":
                # Wyłącz wideo
                participant.video_enabled = False
                await webrtc_session.set_video_enabled(False)
                
                # Powiadom innych uczestników
                await broadcast_participant_state(participant)
            
            elif message_type == "enable_video":
                # Włącz wideo
                participant.video_enabled = True
                await webrtc_session.set_video_enabled(True)
                
                # Powiadom innych uczestników
                await broadcast_participant_state(participant)
                
            elif message_type == "signaling":
                # Obsługa sygnalizacji WebRTC
                await webrtc_session.handle_signaling_message(message.get("data"))
    
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        # Obsługa rozłączenia
        if session_id in webrtc_sessions:
            await webrtc_sessions[session_id].disconnect_signaling()

# Funkcja pomocnicza do rozgłaszania stanu uczestnika
async def broadcast_participant_state(participant: Participant):
    room_id = participant.room_id
    if room_id not in active_rooms:
        return
    
    room = active_rooms[room_id]
    message = {
        "type": "participant_state_change",
        "participant_id": participant.user_id,
        "name": participant.name,
        "audio_enabled": participant.audio_enabled,
        "video_enabled": participant.video_enabled
    }
    
    # Roześlij do wszystkich uczestników pokoju
    for user_id in room.participants:
        if user_id in active_participants:
            other_participant = active_participants[user_id]
            other_session_id = other_participant.session_id
            if other_session_id in webrtc_sessions:
                session = webrtc_sessions[other_session_id]
                if session.signaling_connected:
                    await session.send_signaling_message(message)
```

### 4. Funkcje administracyjne i monitorowanie

```python
# Funkcje administracyjne i monitorowanie

@api.get("/admin/stats", dependencies=[Depends(verify_token)])
async def get_stats():
    """Pobierz statystyki systemu."""
    return {
        "active_rooms": len(active_rooms),
        "active_participants": len(active_participants),
        "webrtc_sessions": len(webrtc_sessions),
        "system_stats": app_rtaspi.get_system_stats()
    }

@api.get("/admin/rooms", dependencies=[Depends(verify_token)])
async def get_all_rooms():
    """Pobierz listę aktywnych pokojów."""
    return {
        "rooms": [
            {
                "room_id": room.room_id,
                "name": room.name,
                "owner_id": room.owner_id,
                "participants_count": len(room.participants),
                "recording": room.recording,
                "created_at": room.created_at
            }
            for room in active_rooms.values()
        ]
    }

@api.get("/admin/participants", dependencies=[Depends(verify_token)])
async def get_all_participants():
    """Pobierz listę aktywnych uczestników."""
    return {
        "participants": [
            {
                "user_id": p.user_id,
                "name": p.name,
                "room_id": p.room_id,
                "audio_enabled": p.audio_enabled,
                "video_enabled": p.video_enabled,
                "joined_at": p.joined_at
            }
            for p in active_participants.values()
        ]
    }

@api.get("/admin/rooms/{room_id}/participants", dependencies=[Depends(verify_token)])
async def get_room_participants(room_id: str):
    """Pobierz uczestników konkretnego pokoju."""
    if room_id not in active_rooms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    room = active_rooms[room_id]
    participants = []
    
    for user_id in room.participants:
        if user_id in active_participants:
            p = active_participants[user_id]
            participants.append({
                "user_id": p.user_id,
                "name": p.name,
                "audio_enabled": p.audio_enabled,
                "video_enabled": p.video_enabled,
                "joined_at": p.joined_at
            })
    
    return {"participants": participants}

# Funkcja główna
if __name__ == "__main__":
    import uvicorn
    
    # Uruchom serwer FastAPI na porcie 8000
    uvicorn.run(api, host="0.0.0.0", port=8000)
```

## Implementacja front-endu (React)

Oto przykładowa implementacja interfejsu użytkownika w React:

```jsx
// ConferenceRoom.jsx
import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Grid, Box, Typography, Paper, IconButton } from '@mui/material';
import { 
  Mic, MicOff, Videocam, VideocamOff, ScreenShare, 
  StopScreenShare, People, Chat, ExitToApp, FiberManualRecord 
} from '@mui/icons-material';

import { useAuth } from '../contexts/AuthContext';
import { RTASPIClient } from '../lib/rtaspi-client';
import VideoParticipant from '../components/VideoParticipant';
import ParticipantsList from '../components/ParticipantsList';
import ChatPanel from '../components/ChatPanel';

const ConferenceRoom = () => {
  const { roomId } = useParams();
  const { user, token } = useAuth();
  
  const [rtaspi, setRtaspi] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [screenShareEnabled, setScreenShareEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [showParticipants, setShowParticipants] = useState(false);
  const [showChat, setShowChat] = useState(false);
  
  const localVideoRef = useRef(null);
  const websocketRef = useRef(null);
  
  // Inicjalizacja połączenia
  useEffect(() => {
    const initializeConference = async () => {
      try {
        // Dołącz do pokoju
        const response = await fetch(`/api/rooms/${roomId}/join`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
        
        // Połącz z serwerem sygnalizacyjnym
        const wsUrl = `ws://${window.location.host}/ws/conference/${data.session_id}`;
        websocketRef.current = new WebSocket(wsUrl);
        
        websocketRef.current.onopen = () => {
          // Wyślij token uwierzytelniania
          websocketRef.current.send(JSON.stringify({
            type: 'auth',
            token: token
          }));
          
          // Przekaż websocket do klienta RTASPI do sygnalizacji
          rtaspiInstance.setSignalingChannel(websocketRef.current);
        };
        
        setRtaspi(rtaspiInstance);
        
        // Rozpocznij połączenie WebRTC
        await rtaspiInstance.connect();
      } catch (error) {
        console.error('Failed to initialize conference:', error);
      }
    };
    
    if (roomId && token) {
      initializeConference();
    }
    
    // Cleanup przy odmontowaniu komponentu
    return () => {
      if (rtaspi) {
        rtaspi.disconnect();
      }
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      
      // Opuść pokój
      if (token && roomId) {
        fetch(`/api/rooms/${roomId}/leave`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }).catch(err => console.error('Error leaving room:', err));
      }
    };
  }, [roomId, token]);
  
  // Obsługa lokalnego strumienia wideo
  const handleLocalStream = (stream) => {
    if (localVideoRef.current) {
      localVideoRef.current.srcObject = stream;
    }
  };
  
  // Obsługa dołączania nowego uczestnika
  const handleParticipantJoined = (participant) => {
    setParticipants(prev => [...prev, participant]);
  };
  
  // Obsługa opuszczenia przez uczestnika
  const handleParticipantLeft = (participantId) => {
    setParticipants(prev => prev.filter(p => p.id !== participantId));
  };
  
  // Obsługa zmiany stanu uczestnika
  const handleParticipantStateChange = (participant) => {
    setParticipants(prev => 
      prev.map(p => p.id === participant.id ? { ...p, ...participant } : p)
    );
  };
  
  // Przełączanie mikrofonu
  const toggleMicrophone = async () => {
    if (!rtaspi) return;
    
    const newState = !audioEnabled;
    await rtaspi.setAudioEnabled(newState);
    setAudioEnabled(newState);
    
    // Wyślij informację do innych uczestników
    if (websocketRef.current) {
      websocketRef.current.send(JSON.stringify({
        type: newState ? 'unmute_audio' : 'mute_audio'
      }));
    }
  };
  
  // Przełączanie kamery
  const toggleCamera = async () => {
    if (!rtaspi) return;
    
    const newState = !videoEnabled;
    await rtaspi.setVideoEnabled(newState);
    setVideoEnabled(newState);
    
    // Wyślij informację do innych uczestników
    if (websocketRef.current) {
      websocketRef.current.send(JSON.stringify({
        type: newState ? 'enable_video' : 'disable_video'
      }));
    }
  };
  
  // Przełączanie udostępniania ekranu
  const toggleScreenShare = async () => {
    if (!rtaspi) return;
    
    try {
      if (!screenShareEnabled) {
        await rtaspi.startScreenShare();
      } else {
        await rtaspi.stopScreenShare();
      }
      setScreenShareEnabled(!screenShareEnabled);
    } catch (error) {
      console.error('Error toggling screen share:', error);
    }
  };
  
  // Przełączanie nagrywania
  const toggleRecording = async () => {
    if (!rtaspi) return;
    
    try {
      if (!isRecording) {
        const response = await fetch(`/api/rooms/${roomId}/start-recording`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Failed to start recording');
        }
      } else {
        const response = await fetch(`/api/rooms/${roomId}/stop-recording`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Failed to stop recording');
        }
      }
      
      setIsRecording(!isRecording);
    } catch (error) {
      console.error('Error toggling recording:', error);
    }
  };
  
  // Stosowanie filtrów wideo
  const applyVideoFilter = (filterType, filterParams = {}) => {
    if (!rtaspi || !websocketRef.current) return;
    
    websocketRef.current.send(JSON.stringify({
      type: 'video_filter',
      filter: filterType,
      params: filterParams
    }));
  };
  
  // Opuszczanie pokoju
  const leaveRoom = async () => {
    // Implementacja znajduje się w cleanup useEffect
    window.location.href = '/dashboard';
  };
  
  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Nagłówek */}
      <Box sx={{ p: 2, borderBottom: '1px solid #ddd', display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="h6">Room: {roomId}</Typography>
        <Box>
          <IconButton color={isRecording ? "error" : "default"} onClick={toggleRecording}>
            <FiberManualRecord />
          </IconButton>
          <IconButton onClick={() => setShowParticipants(!showParticipants)}>
            <People />
          </IconButton>
          <IconButton onClick={() => setShowChat(!showChat)}>
            <Chat />
          </IconButton>
          <Button 
            variant="contained" 
            color="error" 
            startIcon={<ExitToApp />}
            onClick={leaveRoom}
          >
            Leave
          </Button>
        </Box>
      </Box>
      
      {/* Główna zawartość */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Siatka uczestników */}
        <Box sx={{ flex: 1, p: 2, overflow: 'auto' }}>
          <Grid container spacing={2}>
            {/* Lokalny widok */}
            <Grid item xs={12} md={participants.length > 3 ? 6 : 4}>
              <Paper elevation={3} sx={{ position: 'relative', height: 0, paddingBottom: '56.25%' }}>
                <video 
                  ref={localVideoRef} 
                  autoPlay 
                  muted 
                  style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <Box sx={{ position: 'absolute', bottom: 10, left: 10 }}>
                  <Typography variant="body2" sx={{ color: 'white', backgroundColor: 'rgba(0,0,0,0.5)', padding: '2px 5px', borderRadius: '3px' }}>
                    You ({screenShareEnabled ? 'Screen' : ''})
                  </Typography>
                </Box>
              </Paper>
            </Grid>
            
            {/* Pozostali uczestnicy */}
            {participants.map((participant) => (
              <Grid item xs={12} md={participants.length > 3 ? 6 : 4} key={participant.id}>
                <VideoParticipant 
                  participant={participant}
                  rtaspi={rtaspi}
                />
              </Grid>
            ))}
          </Grid>
        </Box>
        
        {/* Panele boczne */}
        {showParticipants && (
          <Box sx={{ width: 250, borderLeft: '1px solid #ddd', p: 2 }}>
            <ParticipantsList 
              participants={participants} 
              currentUserId={user.id}
            />
          </Box>
        )}
        
        {showChat && (
          <Box sx={{ width: 300, borderLeft: '1px solid #ddd', display: 'flex', flexDirection: 'column' }}>
            <ChatPanel 
              roomId={roomId} 
              sessionId={sessionId}
              websocket={websocketRef.current}
            />
          </Box>
        )}
      </Box>
      
      {/* Kontrolki */}
      <Box sx={{ p: 2, borderTop: '1px solid #ddd', display: 'flex', justifyContent: 'center', gap: 2 }}>
        <IconButton 
          size="large"
          color={audioEnabled ? "primary" : "error"}
          onClick={toggleMicrophone}
        >
          {audioEnabled ? <Mic /> : <MicOff />}
        </IconButton>
        
        <IconButton 
          size="large"
          color={videoEnabled ? "primary" : "error"}
          onClick={toggleCamera}
        >
          {videoEnabled ? <Videocam /> : <VideocamOff />}
        </IconButton>
        
        <IconButton 
          size="large"
          color={screenShareEnabled ? "secondary" : "default"}
          onClick={toggleScreenShare}
        >
          {screenShareEnabled ? <StopScreenShare /> : <ScreenShare />}
        </IconButton>
        
        <Button
          variant="outlined"
          onClick={() => applyVideoFilter('background_blur', { strength: 0.7 })}
        >
          Blur Background
        </Button>
        
        <Button
          variant="outlined"
          onClick={() => applyVideoFilter('reset')}
        >
          Reset Filters
        </Button>
      </Box>
    </Box>
  );
};

export default ConferenceRoom;
```

## Biblioteka kliencka RTASPI

Poniżej przykładowa implementacja klasy klienta RTASPI dla front-endu:

```javascript
// rtaspi-client.js
export class RTASPIClient {
  constructor(options) {
    this.webrtcConfig = options.webrtcConfig;
    this.connection = null;
    this.localStream = null;
    this.screenStream = null;
    this.remoteStreams = new Map();
    this.signalingChannel = null;
    
    // Callbacki
    this.onParticipantJoined = options.onParticipantJoined || (() => {});
    this.onParticipantLeft = options.onParticipantLeft || (() => {});
    this.onParticipantStateChange = options.onParticipantStateChange || (() => {});
    this.onLocalStream = options.onLocalStream || (() => {});
    
    // Bindy dla metod
    this._handleSignalingMessage = this._handleSignalingMessage.bind(this);
  }
  
  // Ustawia kanał sygnalizacyjny
  setSignalingChannel(websocket) {
    this.signalingChannel = websocket;
    this.signalingChannel.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this._handleSignalingMessage(message);
    };
  }
  
  // Obsługuje wiadomości sygnalizacyjne
  _handleSignalingMessage(message) {
    if (message.type === 'signaling') {
      // Obsługa sygnalizacji WebRTC (SDP, ICE)
      const signalingData = message.data;
      
      if (signalingData.type === 'offer') {
        this._handleOffer(signalingData);
      } else if (signalingData.type === 'answer') {
        this._handleAnswer(signalingData);
      } else if (signalingData.type === 'ice-candidate') {
        this._handleIceCandidate(signalingData);
      }
    } else if (message.type === 'participant_state_change') {
      // Obsługa zmiany stanu uczestnika
      this.onParticipantStateChange({
        id: message.participant_id,
        name: message.name,
        audioEnabled: message.audio_enabled,
        videoEnabled: message.video_enabled
      });
    } else if (message.type === 'participant_joined') {
      // Obsługa dołączania uczestnika
      this.onParticipantJoined({
        id: message.participant_id,
        name: message.name,
        audioEnabled: message.audio_enabled,
        videoEnabled: message.video_enabled
      });
    } else if (message.type === 'participant_left') {
      // Obsługa opuszczania przez uczestnika
      this.onParticipantLeft(message.participant_id);
    }
  }
  
  // Nawiązuje połączenie WebRTC
  async connect() {
    // Utwórz połączenie WebRTC
    this.connection = new RTCPeerConnection({
      iceServers: this.webrtcConfig.iceServers
    });
    
    // Dodaj obsługę kanałów ICE
    this.connection.onicecandidate = (event) => {
      if (event.candidate && this.signalingChannel) {
        this.signalingChannel.send(JSON.stringify({
          type: 'signaling',
          data: {
            type: 'ice-candidate',
            candidate: event.candidate
          }
        }));
      }
    };
    
    // Obsługa strumieni zdalnych
    this.connection.ontrack = (event) => {
      const stream = event.streams[0];
      const participantId = stream.id;
      
      this.remoteStreams.set(participantId, stream);
      
      // Powiadom o nowym strumieniu
      this.onParticipantJoined({
        id: participantId,
        stream: stream,
        audioEnabled: true,
        videoEnabled: true
      });
    };
    
    // Uzyskaj lokalny strumień
    this.localStream = await navigator.mediaDevices.getUserMedia({
      audio: true,
      video: true
    });
    
    // Dodaj lokalne ścieżki do połączenia
    this.localStream.getTracks().forEach(track => {
      this.connection.addTrack(track, this.localStream);
    });
    
    // Powiadom o lokalnym strumieniu
    this.onLocalStream(this.localStream);
    
    // Utwórz ofertę
    const offer = await this.connection.createOffer();
    await this.connection.setLocalDescription(offer);
    
    // Wyślij ofertę
    if (this.signalingChannel) {
      this.signalingChannel.send(JSON.stringify({
        type: 'signaling',
        data: {
          type: 'offer',
          sdp: offer
        }
      }));
    }
  }
  
  // Rozłącza połączenie
  disconnect() {
    // Zatrzymaj wszystkie strumienie
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
    }
    
    if (this.screenStream) {
      this.screenStream.getTracks().forEach(track => track.stop());
    }
    
    // Zamknij połączenie
    if (this.connection) {
      this.connection.close();
    }
  }
  
  // Obsługa oferty
  async _handleOffer(offer) {
    if (!this.connection) return;
    
    await this.connection.setRemoteDescription(new RTCSessionDescription(offer.sdp));
    
    // Utwórz odpowiedź
    const answer = await this.connection.createAnswer();
    await this.connection.setLocalDescription(answer);
    
    // Wyślij odpowiedź
    if (this.signalingChannel) {
      this.signalingChannel.send(JSON.stringify({
        type: 'signaling',
        data: {
          type: 'answer',
          sdp: answer
        }
      }));
    }
  }
  
  // Obsługa odpowiedzi
  async _handleAnswer(answer) {
    if (!this.connection) return;
    
    await this.connection.setRemoteDescription(new RTCSessionDescription(answer.sdp));
  }
  
  // Obsługa kandydatów ICE
  async _handleIceCandidate(data) {
    if (!this.connection) return;
    
    try {
      await this.connection.addIceCandidate(new RTCIceCandidate(data.candidate));
    } catch (error) {
      console.error('Error adding ICE candidate:', error);
    }
  }
  
  // Włącza/wyłącza audio
  async setAudioEnabled(enabled) {
    if (!this.localStream) return;
    
    this.localStream.getAudioTracks().forEach(track => {
      track.enabled = enabled;
    });
  }
  
  // Włącza/wyłącza wideo
  async setVideoEnabled(enabled) {
    if (!this.localStream) return;
    
    this.localStream.getVideoTracks().forEach(track => {
      track.enabled = enabled;
    });
  }
  
  // Uruchamia udostępnianie ekranu
  async startScreenShare() {
    try {
      this.screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: true
      });
      
      // Zastąp ścieżki wideo
      const videoSender = this.connection.getSenders().find(sender => 
        sender.track && sender.track.kind === 'video'
      );
      
      if (videoSender) {
        videoSender.replaceTrack(this.screenStream.getVideoTracks()[0]);
      }
      
      // Zatrzymaj udostępnianie po zamknięciu przez użytkownika
      this.screenStream.getVideoTracks()[0].onended = () => {
        this.stopScreenShare();
      };
      
      // Powiadom o zmianie strumienia
      this.onLocalStream(this.screenStream);
      
      return true;
    } catch (error) {
      console.error('Error starting screen share:', error);
      return false;
    }
  }
  
  // Zatrzymuje udostępnianie ekranu
  async stopScreenShare() {
    if (!this.screenStream || !this.localStream) return false;
    
    // Zatrzymaj strumień ekranu
    this.screenStream.getTracks().forEach(track => track.stop());
    
    // Przywróć ścieżkę wideo z kamery
    const videoSender = this.connection.getSenders().find(sender => 
      sender.track && sender.track.kind === 'video'
    );
    
    if (videoSender && this.localStream.getVideoTracks().length > 0) {
      videoSender.replaceTrack(this.localStream.getVideoTracks()[0]);
    }
    
    // Powiadom o zmianie strumienia
    this.onLocalStream(this.localStream);
    
    this.screenStream = null;
    return true;
  }
}
```

## Porównanie z komercyjnymi rozwiązaniami

### RTASPI vs. Komercyjne platformy wideokonferencji

| Cecha | Zoom / Teams / WebEx | RTASPI Custom Solution |
|-------|----------------------|------------------------|
| Koszty | Licencje od 15-30 USD/miesiąc/użytkownika | Jednorazowy koszt deweloperski + hosting |
| Skalowalność | Ograniczona planami subskrypcji | Nieograniczona, zależna od infrastruktury |
| Dostosowanie UI | Bardzo ograniczone | Pełna swoboda |
| Przetwarzanie obrazu | Podstawowe filtry | Zaawansowane algorytmy, własne filtry |
| Integracja | Ograniczone API | Pełna integracja z istniejącymi systemami |
| Prywatność danych | Dane przechowywane przez dostawcę | Pełna kontrola nad danymi |
| SLA | Zależne od dostawcy | Definiowane przez organizację |

### Scenariusze przewagi RTASPI

1. **Branże o wysokich wymaganiach prywatności**:
   - Ochrona zdrowia: Bezpieczne telekonferencje z pacjentami
   - Finanse: Konsultacje z klientami z zachowaniem poufności
   - Prawo: Wideokonferencje objęte tajemnicą adwokacką

2. **Specjalistyczne zastosowania**:
   - Edukacja: Zintegrowane systemy e-learningowe z zaawansowaną telemetrią
   - Telemedycyna: Integracja z systemami EMR i urządzeniami medycznymi
   - Przemysł 4.0: Konferencje z nakładkami AR/VR i integracją IoT

3. **Korporacje z własną infrastrukturą**:
   - Wdrożenia on-premise dla dużych organizacji
   - Zintegrowane z Active Directory/LDAP
   - Dostosowane do brandingu korporacyjnego

## Kluczowe przewagi implementacji RTASPI

1. **Kontrola nad kosztami**: Brak opłat za użytkownika, płacisz tylko za hostowanie
2. **Elastyczność rozwoju**: Możliwość dodawania funkcji według potrzeb biznesowych
3. **Głęboka integracja**: Bezproblemowa integracja z istniejącymi systemami
4. **Zaawansowane przetwarzanie**: Możliwość implementacji algorytmów ML/AI dla filtrów i analizy
5. **Prywatność i bezpieczeństwo**: Pełna kontrola nad przesyłanymi i przechowywanymi danymi
        
        if (!response.ok) {
          throw new Error('Failed to join room');
        }
        
        const data = await response.json();
        setSessionId(data.session_id);
        
        // Inicjalizuj klienta RTASPI
        const rtaspiInstance = new RTASPIClient({
          webrtcConfig: data.webrtc_config,
          onParticipantJoined: handleParticipantJoined,
          onParticipantLeft: handleParticipantLeft,
          onParticipantStateChange: handleParticipantStateChange,
          onLocalStream: handleLocalStream
        });