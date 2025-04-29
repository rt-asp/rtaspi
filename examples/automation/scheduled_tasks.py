#!/usr/bin/env python3
"""
Example demonstrating RTASPI's scheduled task capabilities.
Shows how to implement time-based triggers, recurring tasks,
conditional execution, and task management.
"""

import argparse
import asyncio
import yaml
import signal
import sys
from datetime import datetime, time
from rtaspi.device_managers.base import DeviceManager
from rtaspi.automation.triggers.device import DeviceTrigger
from rtaspi.automation.actions.device import DeviceAction

class ScheduledTaskManager:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self.device_manager = DeviceManager()
        self.tasks = {}
        self.running = False

    def _load_config(self, config_path):
        """Load schedule configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _parse_time(self, time_str):
        """Parse time string in HH:MM format."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except ValueError as e:
            print(f"Error parsing time {time_str}: {e}")
            return None

    def _check_day_condition(self, days):
        """Check if current day matches the schedule."""
        if not days:
            return True
        current_day = datetime.now().strftime('%a').lower()
        return current_day in [day.lower() for day in days]

    def _check_time_range(self, time_range):
        """Check if current time is within the specified range."""
        if not time_range:
            return True
        
        current_time = datetime.now().time()
        start_time = self._parse_time(time_range[0])
        end_time = self._parse_time(time_range[1])
        
        if start_time and end_time:
            # Handle time ranges that cross midnight
            if start_time > end_time:
                return current_time >= start_time or current_time <= end_time
            return start_time <= current_time <= end_time
        
        return True

    async def setup_tasks(self):
        """Set up scheduled tasks from configuration."""
        for task in self.config.get('tasks', []):
            name = task.get('name')
            if not name:
                print("Task missing name, skipping")
                continue

            schedule = task.get('schedule', {})
            trigger_config = {
                'type': 'time',
                'interval': schedule.get('interval'),
                'at': schedule.get('at'),
                'days': schedule.get('days', []),
                'time_range': schedule.get('time_range')
            }

            actions = []
            for action_config in task.get('actions', []):
                action_type = action_config.get('type')
                if action_type == 'device_control':
                    action = DeviceAction(
                        action_type='control',
                        params={
                            'device': action_config['device'],
                            'command': action_config['command'],
                            'params': action_config.get('params', {})
                        }
                    )
                    actions.append(action)
                else:
                    print(f"Unknown action type: {action_type}")

            if actions:
                self.tasks[name] = {
                    'trigger': trigger_config,
                    'actions': actions,
                    'conditions': task.get('conditions', {}),
                    'last_run': None
                }
                print(f"Registered task: {name}")

    async def execute_task(self, name, task):
        """Execute a scheduled task."""
        print(f"Executing task: {name}")
        
        # Check conditions
        conditions = task.get('conditions', {})
        if not self._check_day_condition(conditions.get('days')):
            print(f"Task {name} skipped: day condition not met")
            return
        
        if not self._check_time_range(conditions.get('time_range')):
            print(f"Task {name} skipped: time range condition not met")
            return

        # Execute actions
        for action in task['actions']:
            try:
                if isinstance(action, DeviceAction):
                    device_id = action.params['device']
                    command = action.params['command']
                    params = action.params.get('params', {})
                    
                    device = self.device_manager.get_device(device_id)
                    if device:
                        await device.execute_command(command, **params)
                        print(f"Executed {command} on device {device_id}")
                    else:
                        print(f"Device {device_id} not found")
            except Exception as e:
                print(f"Error executing action for task {name}: {e}")

        task['last_run'] = datetime.now()

    async def check_and_execute_tasks(self):
        """Check and execute tasks based on their schedules."""
        while self.running:
            current_time = datetime.now()
            
            for name, task in self.tasks.items():
                trigger = task['trigger']
                
                # Handle different schedule types
                if trigger['type'] == 'time':
                    if trigger.get('at'):
                        # Specific time execution
                        target_time = self._parse_time(trigger['at'])
                        if target_time:
                            current = current_time.time()
                            if (current.hour == target_time.hour and 
                                current.minute == target_time.minute and
                                (not task['last_run'] or 
                                 task['last_run'].date() < current_time.date())):
                                await self.execute_task(name, task)
                    
                    elif trigger.get('interval'):
                        # Interval-based execution
                        interval = trigger['interval']
                        if not task['last_run'] or (
                            current_time - task['last_run']).total_seconds() >= interval:
                            await self.execute_task(name, task)

            # Check every minute
            await asyncio.sleep(60 - current_time.second)

    async def start(self):
        """Start the task scheduler."""
        self.running = True
        print("Starting task scheduler...")
        await self.setup_tasks()
        await self.check_and_execute_tasks()

    async def stop(self):
        """Stop the task scheduler."""
        self.running = False
        print("\nStopping task scheduler...")

async def main():
    parser = argparse.ArgumentParser(description='RTASPI Scheduled Tasks Example')
    parser.add_argument('--schedule', required=True, help='Path to schedule configuration YAML file')
    args = parser.parse_args()

    scheduler = ScheduledTaskManager(args.schedule)

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\nSignal received, shutting down...")
        asyncio.create_task(scheduler.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await scheduler.start()
    except KeyboardInterrupt:
        await scheduler.stop()

if __name__ == '__main__':
    asyncio.run(main())
