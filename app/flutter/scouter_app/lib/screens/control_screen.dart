import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/hud_state.dart';
import '../models/panel_state.dart';
import '../services/llm_service.dart';
import '../services/websocket_service.dart';
import '../theme/scouter_colors.dart';
import '../widgets/action_button_grid.dart';
import '../widgets/ai_chat_button.dart';
import '../widgets/dpad_widget.dart';
import '../widgets/edge_hint_widget.dart';
import '../widgets/fingerprint_button.dart';
import '../widgets/gesture_guide_bar.dart';
import '../widgets/status_bar_widget.dart';
import 'ai_chat_screen.dart';
import 'alpha_keyboard_screen.dart';
import 'device_list_screen.dart';
import 'numpad_screen.dart';
import 'qr_scanner_screen.dart';

class ControlScreen extends StatefulWidget {
  final WebSocketService wsService;
  final LlmService llmService;

  const ControlScreen({
    super.key,
    required this.wsService,
    required this.llmService,
  });

  @override
  State<ControlScreen> createState() => _ControlScreenState();
}

class _ControlScreenState extends State<ControlScreen> {
  // Track previous modes to only react to transitions
  bool _prevNumericMode = false;
  bool _prevDeviceListMode = false;

  void _openNumpad() => _syncPanelState(PanelState.numpad);
  void _closeNumpad() => _syncPanelState(PanelState.base);
  void _openAlpha() => _syncPanelState(PanelState.alpha);
  void _closeAlpha() => _syncPanelState(PanelState.base);
  void _openAiChat() => _syncPanelState(PanelState.aiChat);
  void _closeAiChat() => _syncPanelState(PanelState.base);

  void _syncPanelState(PanelState panel) {
    final hud = context.read<HudConnection>();
    hud.setActivePanel(panel);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ScouterColors.background,
      body: Consumer<HudConnection>(
        builder: (context, hud, _) {
          // Auto-switch panels on state transitions
          WidgetsBinding.instance.addPostFrameCallback((_) {
            // Numpad auto-open/close
            if (hud.numericMode && !_prevNumericMode) {
              _openNumpad();
            } else if (!hud.numericMode && _prevNumericMode) {
              _closeNumpad();
            }
            _prevNumericMode = hud.numericMode;

            // Device list auto-open/close
            final isDeviceList = hud.state == HudState.deviceList;
            if (isDeviceList && !_prevDeviceListMode) {
              _syncPanelState(PanelState.deviceList);
            } else if (!isDeviceList && _prevDeviceListMode) {
              _syncPanelState(PanelState.base);
            }
            _prevDeviceListMode = isDeviceList;
          });

          // Full-screen overlays
          if (hud.activePanel == PanelState.deviceList) {
            return _wrapWithStatusBar(
              DeviceListScreen(wsService: widget.wsService),
            );
          }

          if (hud.activePanel == PanelState.aiChat) {
            return _wrapWithStatusBar(
              AiChatScreen(
                wsService: widget.wsService,
                llmService: widget.llmService,
                onClose: _closeAiChat,
              ),
            );
          }

          if (hud.activePanel == PanelState.alpha) {
            return _wrapWithStatusBar(
              _withSwipeToClose(
                child: AlphaKeyboardScreen(
                  wsService: widget.wsService,
                ),
                // Swipe right to close alpha
                closeDirection: AxisDirection.right,
                onClose: _closeAlpha,
              ),
            );
          }

          if (hud.activePanel == PanelState.numpad) {
            return _wrapWithStatusBar(
              _withSwipeToClose(
                child: NumpadScreen(
                  wsService: widget.wsService,
                  pinMode: hud.numericMode,
                ),
                // Swipe left to close numpad
                closeDirection: AxisDirection.left,
                onClose: hud.numericMode ? null : _closeNumpad,
              ),
            );
          }

          // BASE layout
          return _wrapWithStatusBar(
            _buildBaseContent(context, hud),
          );
        },
      ),
    );
  }

  Widget _wrapWithStatusBar(Widget content) {
    return Column(
      children: [
        const StatusBarWidget(),
        Expanded(child: content),
      ],
    );
  }

  /// Wraps a full-screen panel with edge swipe detection for closing.
  /// Uses a transparent strip on the appropriate edge that captures drags
  /// without interfering with the panel's own buttons.
  Widget _withSwipeToClose({
    required Widget child,
    required AxisDirection closeDirection,
    VoidCallback? onClose,
  }) {
    if (onClose == null) return child;

    final isSwipeRight = closeDirection == AxisDirection.right;

    return Stack(
      children: [
        child,
        // Edge strip for swipe-to-close
        Positioned(
          left: isSwipeRight ? 0 : null,
          right: isSwipeRight ? null : 0,
          top: 0,
          bottom: 0,
          width: 60,
          child: GestureDetector(
            behavior: HitTestBehavior.translucent,
            onHorizontalDragEnd: (details) {
              final velocity = details.velocity.pixelsPerSecond.dx;
              if (isSwipeRight && velocity > 200) {
                onClose();
              } else if (!isSwipeRight && velocity < -200) {
                onClose();
              }
            },
          ),
        ),
      ],
    );
  }

  Widget _buildBaseContent(BuildContext context, HudConnection hud) {
    double dragStartX = 0;

    return Column(
      children: [
        Expanded(
          child: GestureDetector(
            onHorizontalDragStart: (details) {
              dragStartX = details.globalPosition.dx;
            },
            onHorizontalDragEnd: (details) {
              final screenWidth = MediaQuery.of(context).size.width;
              final velocity = details.velocity.pixelsPerSecond.dx;

              // Swipe right from left edge → open numpad
              if (dragStartX < 80 && velocity > 200) {
                _openNumpad();
              }
              // Swipe left from right edge → open alpha
              if (dragStartX > screenWidth - 128 && velocity < -200) {
                _openAlpha();
              }
            },
            behavior: HitTestBehavior.translucent,
            child: Padding(
              padding: const EdgeInsets.only(left: 16, right: 8),
              child: Row(
                children: [
                  // Left edge hint
                  const EdgeHintWidget(
                    label: 'NUMPAD',
                    color: ScouterColors.yellow,
                    isLeft: true,
                  ),
                  // D-pad + AI Chat button
                  Expanded(
                    flex: 3,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        DpadWidget(onEvent: widget.wsService.sendEvent),
                        const SizedBox(height: 12),
                        AiChatButton(onPressed: _openAiChat),
                      ],
                    ),
                  ),
                  // Action buttons (vertical list)
                  Expanded(
                    flex: 2,
                    child: ActionButtonGrid(
                      onEvent: widget.wsService.sendEvent,
                      onScanQr: () => _openQrScanner(context),
                      onUrlInput: () => _showUrlInput(context),
                    ),
                  ),
                  // Fingerprint button
                  Padding(
                    padding: const EdgeInsets.only(right: 40),
                    child: FingerprintButton(
                      onResult: (success) {
                        if (success) {
                          widget.wsService.sendBiometricAuth(success: true);
                        }
                      },
                    ),
                  ),
                  // Right edge hint
                  const EdgeHintWidget(
                    label: 'ALPHA',
                    color: ScouterColors.cyan,
                    isLeft: false,
                  ),
                ],
              ),
            ),
          ),
        ),
        GestureGuideBar(activePanel: hud.activePanel),
      ],
    );
  }

  void _openQrScanner(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => QrScannerScreen(
          onQrLinkDetected: (url) {
            widget.wsService.sendQrLink(url);
            Navigator.of(context).pop();
          },
        ),
      ),
    );
  }

  void _showUrlInput(BuildContext context) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: ScouterColors.surface,
        title: const Text(
          'Enter QR-Link URL',
          style: TextStyle(
            color: ScouterColors.orange,
            fontFamily: 'monospace',
          ),
        ),
        content: TextField(
          controller: controller,
          style: const TextStyle(
            color: ScouterColors.green,
            fontFamily: 'monospace',
          ),
          decoration: const InputDecoration(
            hintText: 'qrlink://v1/device/mqtt/host:port?...',
            hintStyle: TextStyle(color: ScouterColors.gray),
            enabledBorder: OutlineInputBorder(
              borderSide: BorderSide(color: ScouterColors.green),
            ),
            focusedBorder: OutlineInputBorder(
              borderSide: BorderSide(color: ScouterColors.green, width: 2),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text(
              'CANCEL',
              style: TextStyle(color: ScouterColors.red),
            ),
          ),
          TextButton(
            onPressed: () {
              final url = controller.text.trim();
              if (url.startsWith('qrlink://')) {
                widget.wsService.sendQrLink(url);
                Navigator.pop(ctx);
              }
            },
            child: const Text(
              'SEND',
              style: TextStyle(color: ScouterColors.green),
            ),
          ),
        ],
      ),
    );
  }
}
