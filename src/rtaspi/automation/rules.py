"""Rule-based automation system."""

import logging
import threading
import time
import json
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import schedule

from ..core.logging import get_logger

logger = get_logger(__name__)

class Trigger:
    """Base class for rule triggers."""

    def __init__(self, trigger_type: str, config: Dict[str, Any]):
        """Initialize trigger.
        
        Args:
            trigger_type: Type of trigger
            config: Trigger configuration
        """
        self.type = trigger_type
        self.config = config
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def initialize(self) -> bool:
        """Initialize trigger.
        
        Returns:
            bool: True if initialization successful
        """
        return True

    def cleanup(self) -> None:
        """Clean up trigger resources."""
        pass

    def add_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add trigger callback.
        
        Args:
            callback: Function to call when trigger fires
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove trigger callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _fire(self, data: Dict[str, Any]) -> None:
        """Fire trigger with data.
        
        Args:
            data: Trigger event data
        """
        for callback in self._callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in trigger callback: {e}")


class Action:
    """Base class for rule actions."""

    def __init__(self, action_type: str, config: Dict[str, Any]):
        """Initialize action.
        
        Args:
            action_type: Type of action
            config: Action configuration
        """
        self.type = action_type
        self.config = config

    def initialize(self) -> bool:
        """Initialize action.
        
        Returns:
            bool: True if initialization successful
        """
        return True

    def cleanup(self) -> None:
        """Clean up action resources."""
        pass

    def execute(self, data: Dict[str, Any]) -> bool:
        """Execute action.
        
        Args:
            data: Action input data
            
        Returns:
            bool: True if execution successful
        """
        return True


class Condition:
    """Rule condition evaluator."""

    def __init__(self, condition: str):
        """Initialize condition.
        
        Args:
            condition: Condition expression
        """
        self.condition = condition
        self._compiled = compile(condition, '<string>', 'eval')

    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate condition with data.
        
        Args:
            data: Data for condition evaluation
            
        Returns:
            bool: True if condition satisfied
        """
        try:
            # Create evaluation context
            context = {
                'data': data,
                'now': datetime.now(),
                'timedelta': timedelta,
                're': re,
                'len': len,
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'list': list,
                'dict': dict
            }
            
            # Evaluate condition
            result = eval(self._compiled, {"__builtins__": {}}, context)
            return bool(result)

        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False


class Rule:
    """Automation rule."""

    def __init__(self, rule_id: str, config: Dict[str, Any]):
        """Initialize rule.
        
        Args:
            rule_id: Rule identifier
            config: Rule configuration
        """
        self.rule_id = rule_id
        self.config = config
        self.name = config.get('name', rule_id)
        self.description = config.get('description', '')
        self.enabled = config.get('enabled', True)

        # Create triggers
        self.triggers: List[Trigger] = []
        for trigger_config in config.get('triggers', []):
            trigger_type = trigger_config.get('type')
            if trigger_type:
                trigger = self._create_trigger(trigger_type, trigger_config)
                if trigger:
                    self.triggers.append(trigger)

        # Create conditions
        self.conditions: List[Condition] = []
        for condition in config.get('conditions', []):
            if isinstance(condition, str):
                self.conditions.append(Condition(condition))

        # Create actions
        self.actions: List[Action] = []
        for action_config in config.get('actions', []):
            action_type = action_config.get('type')
            if action_type:
                action = self._create_action(action_type, action_config)
                if action:
                    self.actions.append(action)

        # Schedule
        self.schedule = config.get('schedule')
        self._scheduled_job = None

    def initialize(self) -> bool:
        """Initialize rule.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize triggers
            for trigger in self.triggers:
                if not trigger.initialize():
                    return False
                trigger.add_callback(self._handle_trigger)

            # Initialize actions
            for action in self.actions:
                if not action.initialize():
                    return False

            # Set up schedule if configured
            if self.schedule:
                self._setup_schedule()

            return True

        except Exception as e:
            logger.error(f"Error initializing rule {self.rule_id}: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up rule resources."""
        try:
            # Clean up triggers
            for trigger in self.triggers:
                trigger.cleanup()

            # Clean up actions
            for action in self.actions:
                action.cleanup()

            # Clear schedule
            if self._scheduled_job:
                schedule.cancel_job(self._scheduled_job)

        except Exception as e:
            logger.error(f"Error cleaning up rule {self.rule_id}: {e}")

    def _create_trigger(self, trigger_type: str, config: Dict[str, Any]) -> Optional[Trigger]:
        """Create trigger instance.
        
        Args:
            trigger_type: Type of trigger
            config: Trigger configuration
            
        Returns:
            Optional[Trigger]: Created trigger or None
        """
        try:
            # Import trigger class dynamically
            module = __import__(f'rtaspi.automation.triggers.{trigger_type}', fromlist=['Trigger'])
            trigger_class = getattr(module, 'Trigger')
            return trigger_class(trigger_type, config)
        except Exception as e:
            logger.error(f"Error creating trigger {trigger_type}: {e}")
            return None

    def _create_action(self, action_type: str, config: Dict[str, Any]) -> Optional[Action]:
        """Create action instance.
        
        Args:
            action_type: Type of action
            config: Action configuration
            
        Returns:
            Optional[Action]: Created action or None
        """
        try:
            # Import action class dynamically
            module = __import__(f'rtaspi.automation.actions.{action_type}', fromlist=['Action'])
            action_class = getattr(module, 'Action')
            return action_class(action_type, config)
        except Exception as e:
            logger.error(f"Error creating action {action_type}: {e}")
            return None

    def _handle_trigger(self, data: Dict[str, Any]) -> None:
        """Handle trigger event.
        
        Args:
            data: Trigger event data
        """
        if not self.enabled:
            return

        try:
            # Evaluate conditions
            for condition in self.conditions:
                if not condition.evaluate(data):
                    return

            # Execute actions
            for action in self.actions:
                if not action.execute(data):
                    logger.error(f"Action {action.type} failed in rule {self.rule_id}")

        except Exception as e:
            logger.error(f"Error handling trigger in rule {self.rule_id}: {e}")

    def _setup_schedule(self) -> None:
        """Set up rule schedule."""
        try:
            # Parse schedule configuration
            if isinstance(self.schedule, str):
                # Cron-style schedule
                parts = self.schedule.split()
                if len(parts) == 5:
                    minute, hour, day, month, weekday = parts
                    job = schedule.every()
                    
                    # Set minute
                    if minute != '*':
                        job.at(f"{hour.zfill(2)}:{minute.zfill(2)}")
                    
                    # Set day
                    if day != '*':
                        job.day.at(f"{hour.zfill(2)}:{minute.zfill(2)}")
                    
                    # Set weekday
                    if weekday != '*':
                        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                        job.weekday = weekdays[int(weekday)]
                    
                    self._scheduled_job = job.do(self._handle_schedule)

            elif isinstance(self.schedule, dict):
                # Interval-based schedule
                interval = self.schedule.get('interval', 0)
                unit = self.schedule.get('unit', 'minutes')
                
                if interval > 0:
                    job = schedule.every(interval)
                    if unit == 'seconds':
                        job.seconds
                    elif unit == 'minutes':
                        job.minutes
                    elif unit == 'hours':
                        job.hours
                    elif unit == 'days':
                        job.days
                    
                    self._scheduled_job = job.do(self._handle_schedule)

        except Exception as e:
            logger.error(f"Error setting up schedule for rule {self.rule_id}: {e}")

    def _handle_schedule(self) -> None:
        """Handle scheduled execution."""
        self._handle_trigger({'type': 'schedule', 'timestamp': datetime.now()})

    def get_status(self) -> Dict[str, Any]:
        """Get rule status.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            'id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'triggers': [t.type for t in self.triggers],
            'conditions': [c.condition for c in self.conditions],
            'actions': [a.type for a in self.actions],
            'schedule': self.schedule
        }


class RuleEngine:
    """Rule engine for automation."""

    def __init__(self):
        """Initialize rule engine."""
        self._rules: Dict[str, Rule] = {}
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_scheduler = threading.Event()

    def initialize(self) -> bool:
        """Initialize rule engine.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Start scheduler thread
            self._stop_scheduler.clear()
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop)
            self._scheduler_thread.daemon = True
            self._scheduler_thread.start()
            return True

        except Exception as e:
            logger.error(f"Error initializing rule engine: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up rule engine resources."""
        try:
            # Stop scheduler
            if self._scheduler_thread:
                self._stop_scheduler.set()
                self._scheduler_thread.join()
                self._scheduler_thread = None

            # Clean up rules
            for rule in self._rules.values():
                rule.cleanup()
            self._rules.clear()

        except Exception as e:
            logger.error(f"Error cleaning up rule engine: {e}")

    def load_rules(self, rules_file: str) -> bool:
        """Load rules from file.
        
        Args:
            rules_file: Path to rules file
            
        Returns:
            bool: True if rules loaded successfully
        """
        try:
            # Load rules configuration
            with open(rules_file, 'r') as f:
                rules_config = json.load(f)

            # Create rules
            for rule_config in rules_config.get('rules', []):
                rule_id = rule_config.get('id')
                if rule_id:
                    rule = Rule(rule_id, rule_config)
                    if rule.initialize():
                        self._rules[rule_id] = rule

            return True

        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            return False

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get rule by ID.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            Optional[Rule]: Rule if found
        """
        return self._rules.get(rule_id)

    def get_rules(self) -> List[Rule]:
        """Get all rules.
        
        Returns:
            List[Rule]: List of rules
        """
        return list(self._rules.values())

    def add_rule(self, rule_config: Dict[str, Any]) -> Optional[Rule]:
        """Add rule from configuration.
        
        Args:
            rule_config: Rule configuration
            
        Returns:
            Optional[Rule]: Created rule if successful
        """
        try:
            rule_id = rule_config.get('id')
            if not rule_id:
                return None

            if rule_id in self._rules:
                logger.warning(f"Rule {rule_id} already exists")
                return None

            rule = Rule(rule_id, rule_config)
            if rule.initialize():
                self._rules[rule_id] = rule
                return rule

        except Exception as e:
            logger.error(f"Error adding rule: {e}")
            return None

    def remove_rule(self, rule_id: str) -> bool:
        """Remove rule.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            bool: True if rule was removed
        """
        if rule_id in self._rules:
            rule = self._rules[rule_id]
            rule.cleanup()
            del self._rules[rule_id]
            return True
        return False

    def _scheduler_loop(self) -> None:
        """Scheduler loop for time-based rules."""
        while not self._stop_scheduler.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Longer delay on error
