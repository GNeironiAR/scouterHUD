import 'package:flutter_test/flutter_test.dart';
import 'package:scouter_app/models/hud_state.dart';
import 'package:scouter_app/services/llm_service.dart';

void main() {
  group('LlmService', () {
    late LlmService service;

    setUp(() {
      service = LlmService();
    });

    tearDown(() {
      service.dispose();
    });

    test('initial state is not ready and not downloading', () {
      expect(service.isReady, false);
      expect(service.isDownloading, false);
      expect(service.downloadProgress, 0.0);
      expect(service.error, null);
    });

    test('generateResponse returns error when not ready', () async {
      final history = [
        ChatMessage(sender: 'user', text: 'Hello'),
      ];
      final response = await service.generateResponse(history);
      expect(response, contains('not ready'));
    });

    test('generateResponseStream yields error when not ready', () async {
      final history = [
        ChatMessage(sender: 'user', text: 'Hello'),
      ];
      final tokens = <String>[];
      await for (final token in service.generateResponseStream(history)) {
        tokens.add(token);
      }
      expect(tokens.length, 1);
      expect(tokens.first, contains('not ready'));
    });

    test('generateResponseStream with sensorContext yields error when not ready',
        () async {
      final history = [
        ChatMessage(sender: 'user', text: 'What is the temperature?'),
      ];
      final tokens = <String>[];
      await for (final token in service.generateResponseStream(
        history,
        sensorContext: 'Device: Monitor\nData:\n  temp_c: 36.8 C',
      )) {
        tokens.add(token);
      }
      expect(tokens.length, 1);
      expect(tokens.first, contains('not ready'));
    });

    test('generateResponse with sensorContext returns error when not ready',
        () async {
      final history = [
        ChatMessage(sender: 'user', text: 'SpO2?'),
      ];
      final response = await service.generateResponse(
        history,
        sensorContext: 'Device: Monitor\nData:\n  spo2: 97 %',
      );
      expect(response, contains('not ready'));
    });
  });
}
