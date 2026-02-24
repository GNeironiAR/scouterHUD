import 'package:flutter/foundation.dart';

import 'panel_state.dart';

enum HudState {
  disconnected,
  scanning,
  auth,
  connecting,
  streaming,
  deviceList,
  error,
}

class DeviceInfo {
  final String id;
  final String name;
  final String type;
  final String auth;

  DeviceInfo({
    required this.id,
    required this.name,
    required this.type,
    required this.auth,
  });

  factory DeviceInfo.fromJson(Map<String, dynamic> json) {
    return DeviceInfo(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      type: json['type'] as String? ?? 'unknown',
      auth: json['auth'] as String? ?? 'open',
    );
  }
}

class ChatMessage {
  final String sender; // "user" or "ai"
  final String text;
  final DateTime timestamp;

  ChatMessage({
    required this.sender,
    required this.text,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

class SensorContext {
  final String deviceId;
  final String deviceName;
  final String deviceType;
  final Map<String, dynamic> data;
  final Map<String, dynamic> schema;
  final DateTime receivedAt;

  SensorContext({
    required this.deviceId,
    required this.deviceName,
    required this.deviceType,
    required this.data,
    required this.schema,
    DateTime? receivedAt,
  }) : receivedAt = receivedAt ?? DateTime.now();

  /// Build a compact context string for LLM injection (~100-200 tokens).
  String toContextString() {
    final buf = StringBuffer();
    buf.writeln('Device: $deviceName ($deviceType)');
    buf.writeln('Data:');
    for (final entry in data.entries) {
      if (entry.key == 'ts') continue;
      if (entry.key == 'alerts' || entry.key == 'status' ||
          entry.key == 'dtc_codes') continue;
      final fieldSchema = schema[entry.key];
      final unit = fieldSchema is Map ? (fieldSchema['unit'] ?? '') : '';
      buf.writeln('  ${entry.key}: ${entry.value} $unit');
    }
    if (data.containsKey('alerts') && data['alerts'] is List &&
        (data['alerts'] as List).isNotEmpty) {
      buf.writeln('Alerts: ${(data["alerts"] as List).join(", ")}');
    }
    if (data.containsKey('status')) {
      buf.writeln('Status: ${data["status"]}');
    }
    if (data.containsKey('dtc_codes') && data['dtc_codes'] is List &&
        (data['dtc_codes'] as List).isNotEmpty) {
      buf.writeln('DTC: ${(data["dtc_codes"] as List).join(", ")}');
    }
    return buf.toString().trim();
  }
}

class HudConnection extends ChangeNotifier {
  HudState _state = HudState.disconnected;
  bool _isConnected = false;
  String? _deviceName;
  String? _errorMessage;
  bool _numericMode = false;
  PanelState _activePanel = PanelState.base;
  final List<ChatMessage> _chatMessages = [];
  List<DeviceInfo> _deviceList = [];
  int _deviceListSelected = 0;
  String _activeDeviceId = '';
  SensorContext? _sensorContext;

  HudState get state => _state;
  bool get isConnected => _isConnected;
  String? get deviceName => _deviceName;
  String? get errorMessage => _errorMessage;
  bool get numericMode => _numericMode;
  PanelState get activePanel => _activePanel;
  List<ChatMessage> get chatMessages => List.unmodifiable(_chatMessages);
  List<DeviceInfo> get deviceList => List.unmodifiable(_deviceList);
  int get deviceListSelected => _deviceListSelected;
  String get activeDeviceId => _activeDeviceId;
  SensorContext? get sensorContext => _sensorContext;

  void updateState(String stateName, {String? device, String? error}) {
    _state = _parseState(stateName);
    _deviceName = device ?? _deviceName;
    _errorMessage = error;
    notifyListeners();
  }

  String? _connectionError;
  String? get connectionError => _connectionError;

  void setConnected(bool connected, {String? error}) {
    _isConnected = connected;
    _connectionError = error;
    if (!connected) {
      _state = HudState.disconnected;
      _activePanel = PanelState.base;
      _sensorContext = null;
    }
    notifyListeners();
  }

  void setNumericMode(bool numeric) {
    _numericMode = numeric;
    notifyListeners();
  }

  void setActivePanel(PanelState panel) {
    _activePanel = panel;
    notifyListeners();
  }

  void addChatMessage(String sender, String text) {
    _chatMessages.add(ChatMessage(sender: sender, text: text));
    notifyListeners();
  }

  void updateLastAiMessage(String text) {
    if (_chatMessages.isNotEmpty && _chatMessages.last.sender == 'ai') {
      _chatMessages[_chatMessages.length - 1] = ChatMessage(
        sender: 'ai',
        text: text,
        timestamp: _chatMessages.last.timestamp,
      );
      notifyListeners();
    }
  }

  void clearChatMessages() {
    _chatMessages.clear();
    notifyListeners();
  }

  void updateDeviceList(
    List<DeviceInfo> devices,
    int selected,
    String activeId,
  ) {
    _deviceList = devices;
    _deviceListSelected = selected;
    _activeDeviceId = activeId;
    notifyListeners();
  }

  void updateSensorData({
    required String deviceId,
    required String deviceName,
    required String deviceType,
    required Map<String, dynamic> data,
    required Map<String, dynamic> schema,
  }) {
    _sensorContext = SensorContext(
      deviceId: deviceId,
      deviceName: deviceName,
      deviceType: deviceType,
      data: data,
      schema: schema,
    );
    notifyListeners();
  }

  static HudState _parseState(String name) {
    switch (name) {
      case 'scanning':
        return HudState.scanning;
      case 'auth':
        return HudState.auth;
      case 'connecting':
        return HudState.connecting;
      case 'streaming':
        return HudState.streaming;
      case 'device_list':
        return HudState.deviceList;
      case 'error':
        return HudState.error;
      default:
        return HudState.disconnected;
    }
  }
}
