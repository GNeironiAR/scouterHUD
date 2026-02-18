import 'package:flutter_test/flutter_test.dart';
import 'package:scouter_app/models/hud_state.dart';

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
  });
}
