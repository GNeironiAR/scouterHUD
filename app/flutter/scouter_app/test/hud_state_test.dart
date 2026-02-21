import 'package:flutter_test/flutter_test.dart';
import 'package:scouter_app/models/hud_state.dart';
import 'package:scouter_app/models/panel_state.dart';

void main() {
  group('HudConnection', () {
    late HudConnection hud;

    setUp(() {
      hud = HudConnection();
    });

    test('initial state is disconnected', () {
      expect(hud.state, HudState.disconnected);
      expect(hud.isConnected, false);
      expect(hud.numericMode, false);
      expect(hud.deviceName, null);
      expect(hud.errorMessage, null);
      expect(hud.activePanel, PanelState.base);
      expect(hud.chatMessages, isEmpty);
    });

    test('setConnected updates state', () {
      hud.setConnected(true);
      expect(hud.isConnected, true);

      hud.setConnected(false);
      expect(hud.isConnected, false);
      expect(hud.state, HudState.disconnected);
    });

    test('updateState parses scanning', () {
      hud.updateState('scanning');
      expect(hud.state, HudState.scanning);
    });

    test('updateState parses auth', () {
      hud.updateState('auth');
      expect(hud.state, HudState.auth);
    });

    test('updateState parses streaming with device', () {
      hud.updateState('streaming', device: 'monitor-bed-12');
      expect(hud.state, HudState.streaming);
      expect(hud.deviceName, 'monitor-bed-12');
    });

    test('updateState parses error with message', () {
      hud.updateState('error', error: 'Connection failed');
      expect(hud.state, HudState.error);
      expect(hud.errorMessage, 'Connection failed');
    });

    test('updateState unknown defaults to disconnected', () {
      hud.updateState('unknown_state');
      expect(hud.state, HudState.disconnected);
    });

    test('setNumericMode toggles mode', () {
      hud.setNumericMode(true);
      expect(hud.numericMode, true);

      hud.setNumericMode(false);
      expect(hud.numericMode, false);
    });

    test('device name persists across updates', () {
      hud.updateState('streaming', device: 'car-001');
      hud.updateState('streaming');
      expect(hud.deviceName, 'car-001');
    });

    test('notifies listeners on state change', () {
      int notifyCount = 0;
      hud.addListener(() => notifyCount++);

      hud.updateState('scanning');
      expect(notifyCount, 1);

      hud.setConnected(true);
      expect(notifyCount, 2);

      hud.setNumericMode(true);
      expect(notifyCount, 3);
    });

    test('setActivePanel updates panel state', () {
      hud.setActivePanel(PanelState.numpad);
      expect(hud.activePanel, PanelState.numpad);

      hud.setActivePanel(PanelState.alpha);
      expect(hud.activePanel, PanelState.alpha);

      hud.setActivePanel(PanelState.aiChat);
      expect(hud.activePanel, PanelState.aiChat);

      hud.setActivePanel(PanelState.base);
      expect(hud.activePanel, PanelState.base);
    });

    test('setActivePanel notifies listeners', () {
      int notifyCount = 0;
      hud.addListener(() => notifyCount++);

      hud.setActivePanel(PanelState.numpad);
      expect(notifyCount, 1);
    });

    test('disconnect resets panel to base', () {
      hud.setConnected(true);
      hud.setActivePanel(PanelState.aiChat);
      expect(hud.activePanel, PanelState.aiChat);

      hud.setConnected(false);
      expect(hud.activePanel, PanelState.base);
    });

    test('addChatMessage adds messages', () {
      hud.addChatMessage('user', 'Show RPM');
      expect(hud.chatMessages.length, 1);
      expect(hud.chatMessages[0].sender, 'user');
      expect(hud.chatMessages[0].text, 'Show RPM');

      hud.addChatMessage('ai', 'Displaying RPM gauge');
      expect(hud.chatMessages.length, 2);
      expect(hud.chatMessages[1].sender, 'ai');
    });

    test('addChatMessage notifies listeners', () {
      int notifyCount = 0;
      hud.addListener(() => notifyCount++);

      hud.addChatMessage('user', 'test');
      expect(notifyCount, 1);
    });

    test('clearChatMessages clears all messages', () {
      hud.addChatMessage('user', 'msg1');
      hud.addChatMessage('ai', 'msg2');
      expect(hud.chatMessages.length, 2);

      hud.clearChatMessages();
      expect(hud.chatMessages, isEmpty);
    });

    test('chatMessages returns unmodifiable list', () {
      hud.addChatMessage('user', 'test');
      final messages = hud.chatMessages;
      expect(
        () => messages.add(ChatMessage(sender: 'user', text: 'x')),
        throwsUnsupportedError,
      );
    });

    // Device list tests
    test('updateState parses device_list', () {
      hud.updateState('device_list');
      expect(hud.state, HudState.deviceList);
    });

    test('updateDeviceList stores device data', () {
      final devices = [
        DeviceInfo(
            id: 'dev-1', name: 'Device One', type: 'monitor', auth: 'pin'),
        DeviceInfo(
            id: 'dev-2', name: 'Device Two', type: 'sensor', auth: 'open'),
      ];
      hud.updateDeviceList(devices, 0, 'dev-1');
      expect(hud.deviceList.length, 2);
      expect(hud.deviceListSelected, 0);
      expect(hud.activeDeviceId, 'dev-1');
    });

    test('updateDeviceList notifies listeners', () {
      int notifyCount = 0;
      hud.addListener(() => notifyCount++);
      hud.updateDeviceList([], 0, '');
      expect(notifyCount, 1);
    });

    test('deviceList returns unmodifiable list', () {
      hud.updateDeviceList([
        DeviceInfo(id: 'd1', name: 'D1', type: 't', auth: 'open'),
      ], 0, '');
      expect(
        () => hud.deviceList.add(
            DeviceInfo(id: 'x', name: 'x', type: 't', auth: 'open')),
        throwsUnsupportedError,
      );
    });

    test('setActivePanel supports deviceList', () {
      hud.setActivePanel(PanelState.deviceList);
      expect(hud.activePanel, PanelState.deviceList);
    });
  });

  group('DeviceInfo', () {
    test('fromJson parses complete data', () {
      final info = DeviceInfo.fromJson({
        'id': 'monitor-bed-12',
        'name': 'Monitor Bed 12',
        'type': 'medical.monitor',
        'auth': 'pin',
      });
      expect(info.id, 'monitor-bed-12');
      expect(info.name, 'Monitor Bed 12');
      expect(info.type, 'medical.monitor');
      expect(info.auth, 'pin');
    });

    test('fromJson handles missing fields with defaults', () {
      final info = DeviceInfo.fromJson({});
      expect(info.id, '');
      expect(info.name, '');
      expect(info.type, 'unknown');
      expect(info.auth, 'open');
    });
  });
}
