# test_notifier_unit.py - VRAI fichier pytest
import pytest
import asyncio
from server.services.notifier import get_notifier

@pytest.mark.asyncio
async def test_email_critical():
    notifier = get_notifier()
    success = await notifier.send_alert({
        "type": "TEST_CRITICAL",
        "severity": "CRITICAL",
        "source_ip": "1.2.3.4",
        "target_ip": "5.6.7.8",
        "agent_id": "test-agent",
        "timestamp": "2024-01-01T00:00:00"
    })
    assert success is True