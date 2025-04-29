#!/usr/bin/env python3
"""
Example demonstrating RTASPI's rule-based automation capabilities.
Shows how to define automation rules, create triggers and conditions,
configure actions, and handle events.
"""

import argparse
import yaml
from rtaspi.automation.rules import RuleEngine
from rtaspi.automation.triggers.device import MotionTrigger
from rtaspi.automation.triggers.stream import StreamTrigger
from rtaspi.automation.actions.device import DeviceAction
from rtaspi.automation.actions.stream import StreamAction

def load_config(config_path):
    """Load rule configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_rules(config):
    """Set up automation rules from configuration."""
    engine = RuleEngine()
    
    for rule in config['rules']:
        # Create trigger based on type
        if rule['trigger']['type'] == 'motion_detected':
            trigger = MotionTrigger(
                device_id=rule['trigger']['device'],
                sensitivity=rule['trigger'].get('sensitivity', 0.5)
            )
        elif rule['trigger']['type'] == 'temperature_change':
            trigger = StreamTrigger(
                device_id=rule['trigger']['device'],
                threshold=rule['trigger'].get('threshold', 20)
            )
        else:
            print(f"Unknown trigger type: {rule['trigger']['type']}")
            continue

        # Create actions
        actions = []
        for action_config in rule['actions']:
            if action_config['type'] == 'notification':
                action = StreamAction(
                    action_type='notification',
                    params={
                        'method': action_config['method'],
                        'recipient': action_config['recipient']
                    }
                )
            elif action_config['type'] == 'device_control':
                action = DeviceAction(
                    action_type='control',
                    params={
                        'device': action_config['device'],
                        'command': action_config['command']
                    }
                )
            else:
                print(f"Unknown action type: {action_config['type']}")
                continue
            actions.append(action)

        # Add rule to engine
        engine.add_rule(
            name=rule['name'],
            trigger=trigger,
            actions=actions,
            conditions=rule.get('condition', {})
        )

    return engine

def main():
    parser = argparse.ArgumentParser(description='RTASPI Rule-based Automation Example')
    parser.add_argument('--config', required=True, help='Path to rules configuration YAML file')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Setup rule engine
    engine = setup_rules(config)

    # Start rule engine
    print("Starting rule engine...")
    try:
        engine.start()
        
        # Keep running until interrupted
        while True:
            engine.process_events()
    except KeyboardInterrupt:
        print("\nStopping rule engine...")
        engine.stop()

if __name__ == '__main__':
    main()
