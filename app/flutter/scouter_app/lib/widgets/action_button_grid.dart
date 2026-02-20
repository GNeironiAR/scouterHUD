import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/scouter_colors.dart';

class ActionButtonGrid extends StatelessWidget {
  final void Function(String eventName) onEvent;
  final VoidCallback onScanQr;
  final VoidCallback onUrlInput;

  const ActionButtonGrid({
    super.key,
    required this.onEvent,
    required this.onScanQr,
    required this.onUrlInput,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _actionButton('CANCEL', 'cancel', ScouterColors.red),
        const SizedBox(height: 10),
        _actionButton('HOME', 'home', ScouterColors.blue),
        const SizedBox(height: 10),
        _toolButton('QR SCAN', ScouterColors.yellow, onScanQr),
        const SizedBox(height: 10),
        _toolButton('URL', ScouterColors.orange, onUrlInput),
      ],
    );
  }

  Widget _actionButton(String label, String event, Color color) {
    return SizedBox(
      width: 100,
      height: 52,
      child: OutlinedButton(
        style: _buttonStyle(color),
        onPressed: () {
          HapticFeedback.mediumImpact();
          onEvent(event);
        },
        child: _buttonText(label),
      ),
    );
  }

  Widget _toolButton(String label, Color color, VoidCallback onPressed) {
    return SizedBox(
      width: 100,
      height: 52,
      child: OutlinedButton(
        style: _buttonStyle(color),
        onPressed: () {
          HapticFeedback.mediumImpact();
          onPressed();
        },
        child: _buttonText(label),
      ),
    );
  }

  ButtonStyle _buttonStyle(Color color) {
    return OutlinedButton.styleFrom(
      side: BorderSide(color: color, width: 2),
      foregroundColor: color,
      backgroundColor: ScouterColors.surface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      padding: EdgeInsets.zero,
    );
  }

  Widget _buttonText(String label) {
    return Text(
      label,
      style: const TextStyle(
        fontFamily: 'monospace',
        fontSize: 12,
        fontWeight: FontWeight.bold,
      ),
    );
  }
}
