import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/hud_state.dart';
import '../services/websocket_service.dart';
import '../theme/scouter_colors.dart';

class AiChatScreen extends StatefulWidget {
  final WebSocketService wsService;
  final VoidCallback onClose;

  const AiChatScreen({
    super.key,
    required this.wsService,
    required this.onClose,
  });

  @override
  State<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends State<AiChatScreen> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;

    final hud = context.read<HudConnection>();
    hud.addChatMessage('user', text);
    widget.wsService.sendAiChat(text);
    _textController.clear();

    // Scroll to bottom after message is added
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
                      const Text(
                        'Ask the AI assistant anything',
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 12,
                          color: ScouterColors.textDim,
                        ),
                      ),
                    ],
                  ),
                );
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
                        msg.text,
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
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 14,
                    color: ScouterColors.textPrimary,
                  ),
                  decoration: InputDecoration(
                    hintText: 'Type command...',
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
                  ),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 44,
                child: OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(
                      color: ScouterColors.green,
                      width: 2,
                    ),
                    foregroundColor: ScouterColors.green,
                    backgroundColor: ScouterColors.surface,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                  ),
                  onPressed: _sendMessage,
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
}
