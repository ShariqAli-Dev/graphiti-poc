#!/usr/bin/env python3
"""
Quick test to verify SEMAPHORE_LIMIT is being read correctly.
Run this BEFORE starting cli.py to verify the fix.
"""

import os
from dotenv import load_dotenv

# Load .env first (critical!)
load_dotenv()

print("="*80)
print("SEMAPHORE_LIMIT Configuration Test")
print("="*80)

# Check what's in the environment
env_value = os.getenv('SEMAPHORE_LIMIT')
print(f"\n1. SEMAPHORE_LIMIT from .env file: {env_value}")

# Now import graphiti_core (after load_dotenv)
from graphiti_core import helpers

print(f"2. SEMAPHORE_LIMIT used by graphiti_core: {helpers.SEMAPHORE_LIMIT}")

# Verify they match
if env_value and int(env_value) == helpers.SEMAPHORE_LIMIT:
    print(f"\n✓ SUCCESS: graphiti_core is using your configured value ({env_value})")
else:
    print(f"\n✗ FAILED: Mismatch detected!")
    print(f"  Expected: {env_value}")
    print(f"  Got: {helpers.SEMAPHORE_LIMIT}")

print("="*80)
