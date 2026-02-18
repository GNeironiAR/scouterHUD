import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import '../models/hud_state.dart';

class WebSocketService {
  final HudConnection hudConnection;
  WebSocketChannel? _channel;
  Timer? _reconnectTimer;
  String? _url;
  bool _shouldReconnect = false;

  WebSocketService(this.hudConnection);

  bool get isConnected => hudConnection.isConnected;

  void connect(String host, int port) {
    _url = 'ws://$host:$port';
    _shouldReconnect = true;
    _doConnect();
  }

  void disconnect() {
    _shouldReconnect = false;
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
    _channel?.sink.close();
    _channel = null;
    hudConnection.setConnected(false);
  }

  void sendEvent(String eventName) {
    _send({'type': 'input', 'event': eventName});
  }

  void sendQrLink(String url) {
    _send({'type': 'qrlink', 'url': url});
  }

  void _send(Map<String, dynamic> msg) {
    if (_channel != null && hudConnection.isConnected) {
      _channel!.sink.add(jsonEncode(msg));
    }
  }

  Future<void> _doConnect() async {
    if (_url == null) return;

    try {
      final channel = WebSocketChannel.connect(Uri.parse(_url!));

      // Wait for the WebSocket to actually connect
      await channel.ready;

      _channel = channel;
      hudConnection.setConnected(true);

      _channel!.stream.listen(
        (data) => _onMessage(data as String),
        onDone: _onDisconnected,
        onError: (_) => _onDisconnected(),
      );
    } catch (e) {
      hudConnection.setConnected(false, error: '$e');
      _scheduleReconnect();
    }
  }

  void _onMessage(String raw) {
    try {
      final msg = jsonDecode(raw) as Map<String, dynamic>;
      final type = msg['type'] as String?;

      if (type == 'state') {
        hudConnection.updateState(
          msg['state'] as String? ?? '',
          device: msg['device'] as String?,
          error: msg['error'] as String?,
        );
      } else if (type == 'mode') {
        hudConnection.setNumericMode(msg['numeric'] as bool? ?? false);
      }
    } catch (_) {
      // Ignore malformed messages
    }
  }

  void _onDisconnected() {
    _channel = null;
    hudConnection.setConnected(false);
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    if (_shouldReconnect) {
      _reconnectTimer?.cancel();
      _reconnectTimer = Timer(const Duration(seconds: 3), _doConnect);
    }
  }
}
