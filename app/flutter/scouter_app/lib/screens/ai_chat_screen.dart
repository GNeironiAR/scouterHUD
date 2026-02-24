import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/hud_state.dart';
import '../services/llm_service.dart';
import '../services/websocket_service.dart';
import '../theme/scouter_colors.dart';

class AiChatScreen extends StatefulWidget {
  final WebSocketService wsService;
  final LlmService llmService;
  final VoidCallback onClose;

  const AiChatScreen({
    super.key,
    required this.wsService,
    required this.llmService,
    required this.onClose,
  });

  @override
  State<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends State<AiChatScreen> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();
  bool _isGenerating = false;
  StreamSubscription<String>? _streamSub;

  @override
  void dispose() {
    _streamSub?.cancel();
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage() {
    final text = _textController.text.trim();
    if (text.isEmpty || _isGenerating) return;

    final hud = context.read<HudConnection>();
    hud.addChatMessage('user', text);
    _textController.clear();

    if (!widget.llmService.isReady) {
      hud.addChatMessage('ai', 'Model not ready. Please wait for download.');
      _scrollToBottom();
      return;
    }

    setState(() => _isGenerating = true);

    // Add placeholder AI message for streaming
    hud.addChatMessage('ai', '');

    // Inject sensor context from HUD device data
    final sensorCtx = hud.sensorContext?.toContextString();

    final buffer = StringBuffer();
    _streamSub = widget.llmService
        .generateResponseStream(hud.chatMessages, sensorContext: sensorCtx)
        .listen(
      (token) {
        buffer.write(token);
        hud.updateLastAiMessage(buffer.toString());
        _scrollToBottom();
      },
      onDone: () {
        if (buffer.isEmpty) {
          hud.updateLastAiMessage('(no response)');
        }
        setState(() => _isGenerating = false);
        _scrollToBottom();
      },
      onError: (error) {
        hud.updateLastAiMessage('Error: $error');
        setState(() => _isGenerating = false);
        _scrollToBottom();
      },
    );

    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: const BoxDecoration(
            color: ScouterColors.surface,
            border: Border(bottom: BorderSide(color: ScouterColors.border)),
          ),
          child: Row(
            children: [
              const Text(
                '\u25C6 AI ASSISTANT',
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: ScouterColors.purple,
                  letterSpacing: 2,
                ),
              ),
              const SizedBox(width: 8),
              // Model status indicator
              ListenableBuilder(
                listenable: widget.llmService,
                builder: (context, _) {
                  if (widget.llmService.isReady) {
                    return const Text(
                      'LOCAL',
                      style: TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 10,
                        color: ScouterColors.green,
                        fontWeight: FontWeight.bold,
                      ),
                    );
                  }
                  if (widget.llmService.isDownloading) {
                    final pct =
                        (widget.llmService.downloadProgress * 100).toInt();
                    return Text(
                      'DL $pct%',
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 10,
                        color: ScouterColors.yellow,
                        fontWeight: FontWeight.bold,
                      ),
                    );
                  }
                  return const Text(
                    'OFFLINE',
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 10,
                      color: ScouterColors.red,
                      fontWeight: FontWeight.bold,
                    ),
                  );
                },
              ),
              // Sensor context indicator
              Consumer<HudConnection>(
                builder: (context, hud, _) {
                  if (hud.sensorContext != null) {
                    return Flexible(
                      child: Padding(
                        padding: const EdgeInsets.only(left: 6),
                        child: Text(
                          '\u25CF ${hud.sensorContext!.deviceName}',
                          style: const TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 9,
                            color: ScouterColors.cyan,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    );
                  }
                  return const SizedBox.shrink();
                },
              ),
              const Spacer(),
              SizedBox(
                height: 36,
                child: OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: ScouterColors.red, width: 2),
                    foregroundColor: ScouterColors.red,
                    backgroundColor: ScouterColors.surface,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                  ),
                  onPressed: widget.onClose,
                  child: const Text(
                    '\u2715 CLOSE',
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        // Chat messages
        Expanded(
          child: Consumer<HudConnection>(
            builder: (context, hud, _) {
              final messages = hud.chatMessages;

              if (messages.isEmpty) {
                return _buildEmptyState();
              }

              return ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                itemCount: messages.length,
                itemBuilder: (context, index) {
                  final msg = messages[index];
                  final isUser = msg.sender == 'user';

                  return Align(
                    alignment: isUser
                        ? Alignment.centerRight
                        : Alignment.centerLeft,
                    child: Container(
                      constraints: BoxConstraints(
                        maxWidth: MediaQuery.of(context).size.width * 0.6,
                      ),
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: isUser
                            ? ScouterColors.purple.withValues(alpha: 0.2)
                            : ScouterColors.surface,
                        border: Border.all(
                          color: isUser
                              ? ScouterColors.purple.withValues(alpha: 0.4)
                              : ScouterColors.border,
                        ),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        msg.text.isEmpty && !isUser ? '...' : msg.text,
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 13,
                          color: isUser
                              ? ScouterColors.purple
                              : ScouterColors.textPrimary,
                        ),
                      ),
                    ),
                  );
                },
              );
            },
          ),
        ),
        // Input bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: const BoxDecoration(
            color: ScouterColors.surface,
            border: Border(top: BorderSide(color: ScouterColors.border)),
          ),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _textController,
                  enabled: !_isGenerating,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 14,
                    color: ScouterColors.textPrimary,
                  ),
                  decoration: InputDecoration(
                    hintText: _isGenerating ? 'Generating...' : 'Type command...',
                    hintStyle: const TextStyle(color: ScouterColors.gray),
                    filled: true,
                    fillColor: ScouterColors.background,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 8,
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: ScouterColors.border),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(
                        color: ScouterColors.purple,
                        width: 2,
                      ),
                    ),
                    disabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: ScouterColors.border),
                    ),
                  ),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 44,
                child: OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    side: BorderSide(
                      color: _isGenerating
                          ? ScouterColors.gray
                          : ScouterColors.green,
                      width: 2,
                    ),
                    foregroundColor: _isGenerating
                        ? ScouterColors.gray
                        : ScouterColors.green,
                    backgroundColor: ScouterColors.surface,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                  ),
                  onPressed: _isGenerating ? null : _sendMessage,
                  child: const Text(
                    'SEND',
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyState() {
    return ListenableBuilder(
      listenable: widget.llmService,
      builder: (context, _) {
        if (widget.llmService.isDownloading) {
          final pct = (widget.llmService.downloadProgress * 100).toInt();
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(
                  width: 32,
                  height: 32,
                  child: CircularProgressIndicator(
                    color: ScouterColors.purple,
                    strokeWidth: 3,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  'Downloading AI model... $pct%',
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 12,
                    color: ScouterColors.yellow,
                  ),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  width: 200,
                  child: LinearProgressIndicator(
                    value: widget.llmService.downloadProgress,
                    backgroundColor: ScouterColors.surface,
                    color: ScouterColors.purple,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Gemma 3 1B (~500 MB, one-time)',
                  style: TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 10,
                    color: ScouterColors.textDim,
                  ),
                ),
              ],
            ),
          );
        }

        if (widget.llmService.error != null) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  'Failed to load AI model',
                  style: TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 12,
                    color: ScouterColors.red,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  widget.llmService.error!,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 10,
                    color: ScouterColors.textDim,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 12),
                SizedBox(
                  height: 32,
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(
                        color: ScouterColors.yellow,
                        width: 2,
                      ),
                      foregroundColor: ScouterColors.yellow,
                    ),
                    onPressed: () => widget.llmService.initialize(),
                    child: const Text(
                      'RETRY',
                      style: TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          );
        }

        // Ready or loading
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '\u25C6',
                style: TextStyle(
                  fontSize: 36,
                  color: ScouterColors.purple.withValues(alpha: 0.3),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                widget.llmService.isReady
                    ? 'Ask the AI assistant anything'
                    : 'Loading AI model...',
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: ScouterColors.textDim,
                ),
              ),
              if (!widget.llmService.isReady) ...[
                const SizedBox(height: 8),
                const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    color: ScouterColors.purple,
                    strokeWidth: 2,
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}
