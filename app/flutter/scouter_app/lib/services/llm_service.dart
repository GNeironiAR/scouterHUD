import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_gemma/flutter_gemma.dart';

import '../models/hud_state.dart';

/// Local LLM service using flutter_gemma (Gemma 3 1B on-device).
///
/// All inference runs on the phone — no cloud, no network after model download.
/// Model download: tries GitHub Releases first (public repo), falls back to
/// HuggingFace (requires token via --dart-define=HUGGINGFACE_TOKEN).
class LlmService extends ChangeNotifier {
  // Primary: GitHub Releases (works when repo is public, no auth needed)
  static const _githubModelUrl =
      'https://github.com/GNeironiAR/scouterHUD/releases/download/models-v1/gemma3-1b-it-int4.task';

  // Fallback: HuggingFace (requires token for gated models)
  static const _hfModelUrl =
      'https://huggingface.co/litert-community/Gemma3-1B-IT/resolve/main/gemma3-1b-it-int4.task';

  static const _hfToken =
      String.fromEnvironment('HUGGINGFACE_TOKEN', defaultValue: '');

  bool _isReady = false;
  bool _isDownloading = false;
  double _downloadProgress = 0.0;
  String? _error;

  bool get isReady => _isReady;
  bool get isDownloading => _isDownloading;
  double get downloadProgress => _downloadProgress;
  String? get error => _error;

  /// Initialize the LLM: download model on first run, then load it.
  /// Tries GitHub Releases first, falls back to HuggingFace.
  Future<void> initialize() async {
    try {
      _error = null;

      FlutterGemma.initialize(
        huggingFaceToken: _hfToken,
        maxDownloadRetries: 3,
      );

      _isDownloading = true;
      _downloadProgress = 0.0;
      notifyListeners();

      // Try GitHub Releases first (no auth needed when repo is public)
      try {
        await _installFromUrl(_githubModelUrl);
      } catch (_) {
        // Fallback to HuggingFace (needs token)
        _downloadProgress = 0.0;
        notifyListeners();
        await _installFromUrl(_hfModelUrl, token: _hfToken);
      }

      _isDownloading = false;
      _isReady = true;
      _error = null;
      notifyListeners();
    } catch (e) {
      _isDownloading = false;
      _isReady = false;
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<void> _installFromUrl(String url, {String token = ''}) async {
    await FlutterGemma.installModel(modelType: ModelType.gemmaIt)
        .fromNetwork(url, token: token)
        .withProgress((progress) {
          _downloadProgress = progress / 100.0;
          notifyListeners();
        })
        .install();
  }

  /// Generate a response from conversation history using streaming.
  /// Returns a stream of tokens as they are generated.
  Stream<String> generateResponseStream(List<ChatMessage> history) async* {
    if (!_isReady) {
      yield 'Model not ready. Please wait for download to complete.';
      return;
    }

    dynamic model;
    dynamic chat;

    try {
      model = await FlutterGemma.getActiveModel(
        maxTokens: 1024,
        preferredBackend: PreferredBackend.gpu,
      );

      chat = await model.createChat(
        temperature: 0.7,
        topK: 40,
      );

      // Add conversation history (last 10 messages max to fit context)
      final recent = history.length > 10
          ? history.sublist(history.length - 10)
          : history;

      for (final msg in recent) {
        await chat.addQueryChunk(Message.text(
          text: msg.text,
          isUser: msg.sender == 'user',
        ));
      }

      // Stream response tokens
      final completer = Completer<void>();
      final controller = StreamController<String>();

      chat.generateChatResponseAsync().listen(
        (ModelResponse response) {
          if (response is TextResponse) {
            controller.add(response.token);
          }
        },
        onDone: () {
          controller.close();
          completer.complete();
        },
        onError: (error) {
          controller.addError(error);
          controller.close();
          completer.complete();
        },
      );

      yield* controller.stream;
      await completer.future;
    } catch (e) {
      yield 'Error: $e';
    } finally {
      try {
        await chat?.close();
        await model?.close();
      } catch (_) {}
    }
  }

  /// Non-streaming: generate full response at once.
  Future<String> generateResponse(List<ChatMessage> history) async {
    final buffer = StringBuffer();
    await for (final token in generateResponseStream(history)) {
      buffer.write(token);
    }
    return buffer.toString();
  }

  @override
  void dispose() {
    super.dispose();
  }
}
