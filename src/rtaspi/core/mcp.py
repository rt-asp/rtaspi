#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Moduł komunikacji międzymodułowej (MCP - Module Communication Protocol)
"""

import logging
import threading
import json
import time
import uuid
from queue import Queue, Empty

logger = logging.getLogger("MCP")


class MCPBroker:
    """Broker komunikacji międzymodułowej."""

    def __init__(self):
        """
        Inicjalizacja brokera MCP.
        """
        self.topics = {}  # topic -> list of subscribers
        self.clients = {}  # client_id -> MCPClient
        self.lock = threading.RLock()

    def register_client(self, client):
        """
        Rejestruje klienta w brokerze.

        Args:
            client (MCPClient): Klient MCP.
        """
        with self.lock:
            self.clients[client.client_id] = client
            logger.debug(f"Zarejestrowano klienta: {client.client_id}")

    def unregister_client(self, client_id):
        """
        Wyrejestrowuje klienta z brokera.

        Args:
            client_id (str): Identyfikator klienta.
        """
        with self.lock:
            if client_id in self.clients:
                # Usuń klienta z list subskrybentów
                for subscribers in self.topics.values():
                    if client_id in subscribers:
                        subscribers.remove(client_id)

                # Usuń klienta z listy klientów
                del self.clients[client_id]
                logger.debug(f"Wyrejestrowano klienta: {client_id}")

    def subscribe(self, client_id, topic):
        """
        Subskrybuje temat dla klienta.

        Args:
            client_id (str): Identyfikator klienta.
            topic (str): Temat do subskrypcji.
        """
        with self.lock:
            # Sprawdź, czy temat istnieje
            if topic not in self.topics:
                self.topics[topic] = []

            # Dodaj klienta do listy subskrybentów
            if client_id not in self.topics[topic]:
                self.topics[topic].append(client_id)
                logger.debug(f"Klient {client_id} zasubskrybował temat: {topic}")

    def unsubscribe(self, client_id, topic):
        """
        Anuluje subskrypcję tematu dla klienta.

        Args:
            client_id (str): Identyfikator klienta.
            topic (str): Temat do anulowania subskrypcji.
        """
        with self.lock:
            # Sprawdź, czy temat istnieje
            if topic in self.topics:
                # Usuń klienta z listy subskrybentów
                if client_id in self.topics[topic]:
                    self.topics[topic].remove(client_id)
                    logger.debug(
                        f"Klient {client_id} anulował subskrypcję tematu: {topic}"
                    )

                # Usuń temat, jeśli nie ma subskrybentów
                if not self.topics[topic]:
                    del self.topics[topic]

    def publish(self, client_id, topic, message):
        """
        Publikuje wiadomość na temat.

        Args:
            client_id (str): Identyfikator publikującego klienta.
            topic (str): Temat wiadomości.
            message: Treść wiadomości.
        """
        with self.lock:
            # Znajdź wszystkie pasujące tematy
            matching_topics = self._find_matching_topics(topic)

            if not matching_topics:
                logger.debug(f"Brak subskrybentów dla tematu: {topic}")
                return

            # Przygotuj dane wiadomości
            message_data = {
                "topic": topic,
                "sender": client_id,
                "timestamp": time.time(),
                "message_id": str(uuid.uuid4()),
                "payload": message,
            }

            # Doręcz wiadomość do wszystkich subskrybentów
            delivered = 0
            for t in matching_topics:
                for subscriber_id in self.topics[t]:
                    # Nie wysyłaj wiadomości do nadawcy
                    if subscriber_id == client_id:
                        continue

                    # Sprawdź, czy klient istnieje
                    if subscriber_id in self.clients:
                        self.clients[subscriber_id]._receive_message(message_data)
                        delivered += 1

            logger.debug(
                f"Wiadomość opublikowana na temat {topic} doręczona do {delivered} subskrybentów"
            )

    def _find_matching_topics(self, topic):
        """
        Znajduje tematy pasujące do podanego wzorca.

        Args:
            topic (str): Temat lub wzorzec tematu.

        Returns:
            list: Lista pasujących tematów.
        """
        # Obsługa znaków wieloznacznych w tematach
        if "#" in topic:
            # '#' oznacza dowolną liczbę segmentów
            topic_parts = topic.split("/")
            matching_topics = []

            for t in self.topics:
                t_parts = t.split("/")

                # Temat musi mieć odpowiednią liczbę części
                if len(t_parts) < len(topic_parts):
                    continue

                match = True
                for i, part in enumerate(topic_parts):
                    if part == "#":
                        # Pasuje do wszystkich pozostałych segmentów
                        break
                    elif part == "+":
                        # Pasuje do jednego segmentu
                        continue
                    elif i >= len(t_parts) or part != t_parts[i]:
                        match = False
                        break

                if match:
                    matching_topics.append(t)

            return matching_topics
        elif "+" in topic:
            # '+' oznacza dokładnie jeden segment
            topic_parts = topic.split("/")
            matching_topics = []

            for t in self.topics:
                t_parts = t.split("/")

                # Temat musi mieć taką samą liczbę części
                if len(t_parts) != len(topic_parts):
                    continue

                match = True
                for i, part in enumerate(topic_parts):
                    if part == "+":
                        # Pasuje do jednego segmentu
                        continue
                    elif part != t_parts[i]:
                        match = False
                        break

                if match:
                    matching_topics.append(t)

            return matching_topics
        else:
            # Dokładne dopasowanie
            return [topic] if topic in self.topics else []


class MCPClient:
    """Klient komunikacji międzymodułowej."""

    def __init__(self, broker, client_id=None):
        """
        Inicjalizacja klienta MCP.

        Args:
            broker (MCPBroker): Broker MCP.
            client_id (str, optional): Identyfikator klienta. Jeśli None, zostanie wygenerowany.
        """
        self.broker = broker
        self.client_id = client_id or str(uuid.uuid4())
        self.message_queue = Queue()
        self.handlers = {}  # topic pattern -> handler function
        self.running = True
        self.thread = threading.Thread(target=self._message_loop)
        self.thread.daemon = True
        self.thread.start()

        # Rejestracja w brokerze
        self.broker.register_client(self)

    def close(self):
        """Zamyka połączenie klienta."""
        self.running = False
        self.broker.unregister_client(self.client_id)
        self.thread.join(timeout=1)

    def subscribe(self, topic, handler=None):
        """
        Subskrybuje temat.

        Args:
            topic (str): Temat do subskrypcji.
            handler (callable, optional): Funkcja obsługująca wiadomości.
        """
        self.broker.subscribe(self.client_id, topic)

        if handler:
            self.handlers[topic] = handler

    def unsubscribe(self, topic):
        """
        Anuluje subskrypcję tematu.

        Args:
            topic (str): Temat do anulowania subskrypcji.
        """
        self.broker.unsubscribe(self.client_id, topic)

        if topic in self.handlers:
            del self.handlers[topic]

    def publish(self, topic, message):
        """
        Publikuje wiadomość na temat.

        Args:
            topic (str): Temat wiadomości.
            message: Treść wiadomości.
        """
        self.broker.publish(self.client_id, topic, message)

    def _receive_message(self, message_data):
        """
        Otrzymuje wiadomość od brokera i dodaje ją do kolejki.

        Args:
            message_data (dict): Dane wiadomości.
        """
        self.message_queue.put(message_data)

    def _message_loop(self):
        """Główna pętla przetwarzania wiadomości."""
        while self.running:
            try:
                # Pobierz wiadomość z kolejki
                message_data = self.message_queue.get(timeout=0.1)

                # Znajdź pasujący handler
                topic = message_data["topic"]
                payload = message_data["payload"]

                # Sprawdź handlers dla dokładnych dopasowań
                if topic in self.handlers:
                    try:
                        self.handlers[topic](topic, payload)
                    except Exception as e:
                        logger.error(f"Błąd podczas obsługi wiadomości: {e}")
                else:
                    # Sprawdź handlery dla wzorców tematów
                    for pattern, handler in self.handlers.items():
                        if self._topic_matches_pattern(topic, pattern):
                            try:
                                handler(topic, payload)
                            except Exception as e:
                                logger.error(f"Błąd podczas obsługi wiadomości: {e}")
                            break

                self.message_queue.task_done()

            except Empty:
                pass
            except Exception as e:
                logger.error(f"Błąd w pętli przetwarzania wiadomości: {e}")

    def _topic_matches_pattern(self, topic, pattern):
        """
        Sprawdza, czy temat pasuje do wzorca.

        Args:
            topic (str): Temat do sprawdzenia.
            pattern (str): Wzorzec tematu.

        Returns:
            bool: True jeśli temat pasuje do wzorca, False w przeciwnym razie.
        """
        if "#" in pattern:
            # '#' oznacza dowolną liczbę segmentów
            pattern_parts = pattern.split("/")
            topic_parts = topic.split("/")

            # Temat musi mieć odpowiednią liczbę części
            if "#" not in pattern_parts and len(topic_parts) != len(pattern_parts):
                return False

            for i, part in enumerate(pattern_parts):
                if part == "#":
                    # Pasuje do wszystkich pozostałych segmentów
                    return True
                elif part == "+":
                    # Pasuje do jednego segmentu
                    continue
                elif i >= len(topic_parts) or part != topic_parts[i]:
                    return False

            return True
        elif "+" in pattern:
            # '+' oznacza dokładnie jeden segment
            pattern_parts = pattern.split("/")
            topic_parts = topic.split("/")

            # Temat musi mieć taką samą liczbę części
            if len(topic_parts) != len(pattern_parts):
                return False

            for i, part in enumerate(pattern_parts):
                if part == "+":
                    # Pasuje do jednego segmentu
                    continue
                elif part != topic_parts[i]:
                    return False

            return True
        else:
            # Dokładne dopasowanie
            return topic == pattern
