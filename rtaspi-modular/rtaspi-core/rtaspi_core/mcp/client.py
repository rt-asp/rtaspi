#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Module Communication Protocol (MCP) client implementation
"""

import logging
import threading
import time
import uuid
from queue import Queue, Empty

logger = logging.getLogger("MCP")


class MCPBroker:
    """Broker for module communication."""

    def __init__(self):
        """
        Initialize the MCP broker.
        """
        self.topics = {}  # topic -> list of subscribers
        self.clients = {}  # client_id -> MCPClient
        self.lock = threading.RLock()

    def register_client(self, client):
        """
        Register a client with the broker.

        Args:
            client (MCPClient): MCP client.
        """
        with self.lock:
            self.clients[client.client_id] = client
            logger.debug(f"Registered client: {client.client_id}")

    def unregister_client(self, client_id):
        """
        Unregister a client from the broker.

        Args:
            client_id (str): Client identifier.
        """
        with self.lock:
            if client_id in self.clients:
                # Remove client from subscriber lists
                for subscribers in self.topics.values():
                    if client_id in subscribers:
                        subscribers.remove(client_id)

                # Remove client from client list
                del self.clients[client_id]
                logger.debug(f"Unregistered client: {client_id}")

    def subscribe(self, client_id, topic):
        """
        Subscribe to a topic.

        Args:
            client_id (str): Client identifier.
            topic (str): Topic to subscribe to.
        """
        with self.lock:
            # Check if topic exists
            if topic not in self.topics:
                self.topics[topic] = []

            # Add client to subscriber list
            if client_id not in self.topics[topic]:
                self.topics[topic].append(client_id)
                logger.debug(f"Client {client_id} subscribed to topic: {topic}")

    def unsubscribe(self, client_id, topic):
        """
        Unsubscribe from a topic.

        Args:
            client_id (str): Client identifier.
            topic (str): Topic to unsubscribe from.
        """
        with self.lock:
            # Check if topic exists
            if topic in self.topics:
                # Remove client from subscriber list
                if client_id in self.topics[topic]:
                    self.topics[topic].remove(client_id)
                    logger.debug(f"Client {client_id} unsubscribed from topic: {topic}")

                # Remove topic if no subscribers
                if not self.topics[topic]:
                    del self.topics[topic]

    def publish(self, client_id, topic, message):
        """
        Publish a message to a topic.

        Args:
            client_id (str): Publishing client identifier.
            topic (str): Message topic.
            message: Message content.
        """
        with self.lock:
            # Find matching topics
            matching_topics = self._find_matching_topics(topic)

            if not matching_topics:
                logger.debug(f"No subscribers for topic: {topic}")
                return

            # Prepare message data
            message_data = {
                "topic": topic,
                "sender": client_id,
                "timestamp": time.time(),
                "message_id": str(uuid.uuid4()),
                "payload": message,
            }

            # Deliver message to all subscribers
            delivered = 0
            for t in matching_topics:
                for subscriber_id in self.topics[t]:
                    # Don't send message to sender
                    if subscriber_id == client_id:
                        continue

                    # Check if client exists
                    if subscriber_id in self.clients:
                        self.clients[subscriber_id]._receive_message(message_data)
                        delivered += 1

            logger.debug(
                f"Message published to topic {topic} delivered to {delivered} subscribers"
            )

    def _find_matching_topics(self, topic):
        """
        Find topics matching the given pattern.

        Args:
            topic (str): Topic or topic pattern.

        Returns:
            list: List of matching topics.
        """
        # Handle wildcards in topics
        if "#" in topic:
            # '#' means any number of segments
            topic_parts = topic.split("/")
            matching_topics = []

            for t in self.topics:
                t_parts = t.split("/")

                # Topic must have appropriate number of parts
                if len(t_parts) < len(topic_parts):
                    continue

                match = True
                for i, part in enumerate(topic_parts):
                    if part == "#":
                        # Matches all remaining segments
                        break
                    elif part == "+":
                        # Matches one segment
                        continue
                    elif i >= len(t_parts) or part != t_parts[i]:
                        match = False
                        break

                if match:
                    matching_topics.append(t)

            return matching_topics
        elif "+" in topic:
            # '+' means exactly one segment
            topic_parts = topic.split("/")
            matching_topics = []

            for t in self.topics:
                t_parts = t.split("/")

                # Topic must have same number of parts
                if len(t_parts) != len(topic_parts):
                    continue

                match = True
                for i, part in enumerate(topic_parts):
                    if part == "+":
                        # Matches one segment
                        continue
                    elif part != t_parts[i]:
                        match = False
                        break

                if match:
                    matching_topics.append(t)

            return matching_topics
        else:
            # Exact match
            return [topic] if topic in self.topics else []


class MCPClient:
    """Module communication client."""

    def __init__(self, broker, client_id=None):
        """
        Initialize MCP client.

        Args:
            broker (MCPBroker): MCP broker.
            client_id (str, optional): Client identifier. If None, one will be generated.
        """
        self.broker = broker
        self.client_id = client_id or str(uuid.uuid4())
        self.message_queue = Queue()
        self.handlers = {}  # topic pattern -> handler function
        self.running = True
        self.thread = threading.Thread(target=self._message_loop)
        self.thread.daemon = True
        self.thread.start()

        # Register with broker
        self.broker.register_client(self)

    def close(self):
        """Close client connection."""
        self.running = False
        self.broker.unregister_client(self.client_id)
        self.thread.join(timeout=1)

    def subscribe(self, topic, handler=None):
        """
        Subscribe to a topic.

        Args:
            topic (str): Topic to subscribe to.
            handler (callable, optional): Message handler function.
        """
        self.broker.subscribe(self.client_id, topic)

        if handler:
            self.handlers[topic] = handler

    def unsubscribe(self, topic):
        """
        Unsubscribe from a topic.

        Args:
            topic (str): Topic to unsubscribe from.
        """
        self.broker.unsubscribe(self.client_id, topic)

        if topic in self.handlers:
            del self.handlers[topic]

    def publish(self, topic, message):
        """
        Publish a message to a topic.

        Args:
            topic (str): Message topic.
            message: Message content.
        """
        self.broker.publish(self.client_id, topic, message)

    def _receive_message(self, message_data):
        """
        Receive message from broker and add to queue.

        Args:
            message_data (dict): Message data.
        """
        self.message_queue.put(message_data)

    def _message_loop(self):
        """Main message processing loop."""
        while self.running:
            try:
                # Get message from queue
                message_data = self.message_queue.get(timeout=0.1)

                # Find matching handler
                topic = message_data["topic"]
                payload = message_data["payload"]

                # Check handlers for exact matches
                if topic in self.handlers:
                    try:
                        self.handlers[topic](topic, payload)
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")
                else:
                    # Check handlers for topic patterns
                    for pattern, handler in self.handlers.items():
                        if self._topic_matches_pattern(topic, pattern):
                            try:
                                handler(topic, payload)
                            except Exception as e:
                                logger.error(f"Error handling message: {e}")
                            break

                self.message_queue.task_done()

            except Empty:
                pass
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")

    def _topic_matches_pattern(self, topic, pattern):
        """
        Check if topic matches pattern.

        Args:
            topic (str): Topic to check.
            pattern (str): Topic pattern.

        Returns:
            bool: True if topic matches pattern, False otherwise.
        """
        if "#" in pattern:
            # '#' means any number of segments
            pattern_parts = pattern.split("/")
            topic_parts = topic.split("/")

            # Topic must have appropriate number of parts
            if "#" not in pattern_parts and len(topic_parts) != len(pattern_parts):
                return False

            for i, part in enumerate(pattern_parts):
                if part == "#":
                    # Matches all remaining segments
                    return True
                elif part == "+":
                    # Matches one segment
                    continue
                elif i >= len(topic_parts) or part != topic_parts[i]:
                    return False

            return True
        elif "+" in pattern:
            # '+' means exactly one segment
            pattern_parts = pattern.split("/")
            topic_parts = topic.split("/")

            # Topic must have same number of parts
            if len(topic_parts) != len(pattern_parts):
                return False

            for i, part in enumerate(pattern_parts):
                if part == "+":
                    # Matches one segment
                    continue
                elif part != topic_parts[i]:
                    return False

            return True
        else:
            # Exact match
            return topic == pattern
