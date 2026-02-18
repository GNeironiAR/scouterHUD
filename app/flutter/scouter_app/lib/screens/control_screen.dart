import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models/hud_state.dart';
import '../services/websocket_service.dart';
import '../widgets/dpad_widget.dart';
import '../widgets/numpad_widget.dart';
import '../widgets/status_bar_widget.dart';
import 'qr_scanner_screen.dart';

class ControlScreen extends StatelessWidget {
  final WebSocketService wsService;

  const ControlScreen({super.key, required this.wsService});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF111111),
      body: Column(
        children: [
          const StatusBarWidget(),
          // PIN banner
          Consumer<HudConnection>(
            builder: (context, hud, _) {
              if (!hud.numericMode) return const SizedBox.shrink();
              return Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 6),
                color: const Color(0xFF333300),
                child: const Text(
                  'PIN ENTRY \u2014 Type digits, \u232B to delete, SEND to submit',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: Colors.yellow,
                    letterSpacing: 2,
                  ),
                ),
              );
            },
          ),
          // Main content
          Expanded(
            child: Consumer<HudConnection>(
              builder: (context, hud, _) {
                return Padding(
                  padding: const EdgeInsets.only(left: 16, right: 48),
                  child: Row(
                    children: [
                      // D-pad or Numpad
                      Expanded(
                        flex: 3,
                        child: Center(
                          child: hud.numericMode
                              ? NumpadWidget(onEvent: wsService.sendEvent)
                              : DpadWidget(onEvent: wsService.sendEvent),
                        ),
                      ),
                      // Actions + Tools grid
                      Expanded(
                        flex: 2,
                        child: _buildButtonGrid(context, hud.numericMode),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildButtonGrid(BuildContext context, bool numericMode) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _actionButton('CANCEL', 'cancel', Colors.red),
            const SizedBox(width: 10),
            _toolButton(context, 'SCAN QR', Colors.yellow, () => _openQrScanner(context)),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _actionButton('HOME', 'home', Colors.blue),
            const SizedBox(width: 10),
            _toolButton(context, 'URL INPUT', Colors.orange, () => _showUrlInput(context)),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _actionButton('NEXT \u25B6', 'next_device', Colors.grey),
            const SizedBox(width: 10),
            _actionButton('\u25C0 PREV', 'prev_device', Colors.grey),
          ],
        ),
      ],
    );
  }

  Widget _actionButton(String label, String event, Color color) {
    return SizedBox(
      width: 120,
      height: 56,
      child: OutlinedButton(
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: color, width: 2),
          foregroundColor: color,
          backgroundColor: const Color(0xFF1A1A1A),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: EdgeInsets.zero,
        ),
        onPressed: () {
          HapticFeedback.mediumImpact();
          wsService.sendEvent(event);
        },
        child: Text(
          label,
          style: const TextStyle(
            fontFamily: 'monospace',
            fontSize: 13,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _toolButton(
    BuildContext context,
    String label,
    Color color,
    VoidCallback onPressed,
  ) {
    return SizedBox(
      width: 120,
      height: 56,
      child: OutlinedButton(
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: color, width: 2),
          foregroundColor: color,
          backgroundColor: const Color(0xFF1A1A1A),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: EdgeInsets.zero,
        ),
        onPressed: onPressed,
        child: Text(
          label,
          style: const TextStyle(
            fontFamily: 'monospace',
            fontSize: 13,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  void _openQrScanner(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => QrScannerScreen(
          onQrLinkDetected: (url) {
            wsService.sendQrLink(url);
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
        backgroundColor: const Color(0xFF222222),
        title: const Text(
          'Enter QR-Link URL',
          style: TextStyle(color: Colors.yellow, fontFamily: 'monospace'),
        ),
        content: TextField(
          controller: controller,
          style: const TextStyle(color: Colors.green, fontFamily: 'monospace'),
          decoration: const InputDecoration(
            hintText: 'qrlink://v1/device/mqtt/host:port?...',
            hintStyle: TextStyle(color: Color(0xFF555555)),
            enabledBorder: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.green),
            ),
            focusedBorder: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.green, width: 2),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('CANCEL', style: TextStyle(color: Colors.red)),
          ),
          TextButton(
            onPressed: () {
              final url = controller.text.trim();
              if (url.startsWith('qrlink://')) {
                wsService.sendQrLink(url);
                Navigator.pop(ctx);
              }
            },
            child: const Text('SEND', style: TextStyle(color: Colors.green)),
          ),
        ],
      ),
    );
  }
}
