import 'package:flutter/foundation.dart';

enum HudState {
  disconnected,
  scanning,
  auth,
  connecting,
  streaming,
  deviceList,
  error,
}

class HudConnection extends ChangeNotifier {
  HudState _state = HudState.disconnected;
  bool _isConnected = false;
  String? _deviceName;
  String? _errorMessage;
  bool _numericMode = false;

  HudState get state => _state;
  bool get isConnected => _isConnected;
  String? get deviceName => _deviceName;
  String? get errorMessage => _errorMessage;
  bool get numericMode => _numericMode;

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
    }
    notifyListeners();
  }

  void setNumericMode(bool numeric) {
    _numericMode = numeric;
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
