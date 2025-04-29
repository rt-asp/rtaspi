"""SIP (Session Initiation Protocol) implementation."""

import logging
import threading
import queue
import time
from typing import Optional, Dict, Any, List, Callable
import pjsua2 as pj

from ...core.logging import get_logger

logger = get_logger(__name__)

class SIPAccount(pj.Account):
    """SIP account implementation."""

    def __init__(self, callback: Optional[Callable] = None):
        """Initialize SIP account.
        
        Args:
            callback: Callback for account events
        """
        pj.Account.__init__(self)
        self.callback = callback

    def onRegState(self, info: pj.OnRegStateParam) -> None:
        """Handle registration state change.
        
        Args:
            info: Registration state info
        """
        logger.info(f"Registration state: {info.code}/{info.reason}")
        if self.callback:
            self.callback('reg_state', info)

    def onIncomingCall(self, prm: pj.OnIncomingCallParam) -> None:
        """Handle incoming call.
        
        Args:
            prm: Call parameters
        """
        logger.info("Incoming call from " + prm.callId)
        if self.callback:
            self.callback('incoming_call', prm)


class SIPCall(pj.Call):
    """SIP call implementation."""

    def __init__(self, acc: SIPAccount, call_id: Optional[int] = pj.PJSUA_INVALID_ID):
        """Initialize SIP call.
        
        Args:
            acc: SIP account
            call_id: Call ID
        """
        pj.Call.__init__(self, acc, call_id)
        self.account = acc
        self._connected = False
        self._audio_queue = queue.Queue()

    def onCallState(self, prm: pj.OnCallStateParam) -> None:
        """Handle call state change.
        
        Args:
            prm: Call state parameters
        """
        ci = self.getInfo()
        logger.info(f"Call state: {ci.stateText}")
        self._connected = ci.state == pj.PJSIP_INV_STATE_CONFIRMED

    def onCallMediaState(self, prm: pj.OnCallMediaStateParam) -> None:
        """Handle call media state change.
        
        Args:
            prm: Media state parameters
        """
        ci = self.getInfo()
        for mi in ci.media:
            if mi.type == pj.PJMEDIA_TYPE_AUDIO and mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
                self._setupAudio()

    def _setupAudio(self) -> None:
        """Set up audio devices for call."""
        # Get audio media
        aud_med = self.getAudioMedia(-1)
        if not aud_med:
            logger.error("Failed to get audio media")
            return

        # Connect to sound device
        try:
            # Start audio transmission
            aud_med.startTransmit(pj.AudDevManager.instance().getPlaybackDevMedia())
            # Start audio reception
            pj.AudDevManager.instance().getCaptureDevMedia().startTransmit(aud_med)
        except Exception as e:
            logger.error(f"Error setting up audio: {e}")

    def sendAudio(self, audio_data: bytes) -> None:
        """Send audio data.
        
        Args:
            audio_data: Audio samples as bytes
        """
        if not self._connected:
            return

        try:
            self._audio_queue.put(audio_data)
        except Exception as e:
            logger.error(f"Error sending audio: {e}")


class SIPDevice:
    """SIP device implementation."""

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """Initialize SIP device.
        
        Args:
            device_id: Device identifier
            config: Device configuration
        """
        self.device_id = device_id
        self.config = config

        # SIP settings
        self.sip_domain = config.get('sip_domain', '')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.proxy = config.get('proxy', '')
        self.port = config.get('port', 5060)

        # PJSIP objects
        self._ep: Optional[pj.Endpoint] = None
        self._account: Optional[SIPAccount] = None
        self._current_call: Optional[SIPCall] = None

        # State
        self._initialized = False
        self._registered = False

    def initialize(self) -> bool:
        """Initialize SIP device.
        
        Returns:
            bool: True if initialization successful
        """
        if self._initialized:
            return True

        try:
            # Create endpoint
            self._ep = pj.Endpoint()
            self._ep.libCreate()

            # Initialize endpoint
            ep_cfg = pj.EpConfig()
            ep_cfg.uaConfig.userAgent = "rtaspi"
            ep_cfg.logConfig.level = 4
            self._ep.libInit(ep_cfg)

            # Create SIP transport
            tp_cfg = pj.TransportConfig()
            tp_cfg.port = self.port
            self._ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, tp_cfg)

            # Start endpoint
            self._ep.libStart()

            # Create account
            self._account = SIPAccount(self._handle_account_event)
            acc_cfg = pj.AccountConfig()
            acc_cfg.idUri = f"sip:{self.username}@{self.sip_domain}"
            if self.password:
                acc_cfg.regConfig.registrarUri = f"sip:{self.sip_domain}"
                cred = pj.AuthCredInfo("digest", "*", self.username, 0, self.password)
                acc_cfg.sipConfig.authCreds.append(cred)
            if self.proxy:
                acc_cfg.sipConfig.proxies.append(self.proxy)

            self._account.create(acc_cfg)

            self._initialized = True
            logger.info(f"Initialized SIP device {self.device_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize SIP device: {e}")
            self.cleanup()
            return False

    def cleanup(self) -> None:
        """Clean up device resources."""
        try:
            if self._current_call:
                self._current_call.hangup()
                self._current_call = None

            if self._account:
                self._account.delete()
                self._account = None

            if self._ep:
                self._ep.libDestroy()
                self._ep = None

            self._initialized = False
            self._registered = False
            logger.info(f"Cleaned up SIP device {self.device_id}")

        except Exception as e:
            logger.error(f"Error cleaning up SIP device: {e}")

    def make_call(self, destination: str) -> bool:
        """Make outgoing call.
        
        Args:
            destination: SIP URI to call
            
        Returns:
            bool: True if call initiated
        """
        if not self._initialized or not self._registered:
            logger.error("Device not ready")
            return False

        try:
            if self._current_call:
                logger.warning("Call already in progress")
                return False

            self._current_call = SIPCall(self._account)
            self._current_call.makeCall(destination, pj.CallOpParam())
            return True

        except Exception as e:
            logger.error(f"Error making call: {e}")
            return False

    def hangup(self) -> None:
        """Hang up current call."""
        if self._current_call:
            try:
                self._current_call.hangup()
                self._current_call = None
            except Exception as e:
                logger.error(f"Error hanging up: {e}")

    def send_audio(self, audio_data: bytes) -> None:
        """Send audio data.
        
        Args:
            audio_data: Audio samples as bytes
        """
        if self._current_call:
            self._current_call.sendAudio(audio_data)

    def _handle_account_event(self, event: str, data: Any) -> None:
        """Handle account events.
        
        Args:
            event: Event type
            data: Event data
        """
        if event == 'reg_state':
            self._registered = data.code == 200
        elif event == 'incoming_call':
            # Auto-answer incoming calls
            try:
                self._current_call = SIPCall(self._account, data.callId)
                prm = pj.CallOpParam()
                prm.statusCode = 200
                self._current_call.answer(prm)
            except Exception as e:
                logger.error(f"Error answering call: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get device status.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            'id': self.device_id,
            'initialized': self._initialized,
            'registered': self._registered,
            'in_call': self._current_call is not None,
            'sip_domain': self.sip_domain,
            'username': self.username,
            'proxy': self.proxy,
            'port': self.port
        }
