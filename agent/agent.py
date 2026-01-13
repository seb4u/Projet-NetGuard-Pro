from client import SocketClient

client = SocketClient(
    server_host="localhost",
    server_port=9999,
    agent_id="agent-001"
)

client.connect()
client.register()


client.send_alert({
    "type": "PORT_SCAN",
    "source_ip": "192.168.1.10",
    "timestamp": "2026-01-13T15:30:00"
})
