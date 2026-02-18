import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class DpadWidget extends StatelessWidget {
  final void Function(String eventName) onEvent;

  const DpadWidget({
    super.key,
    required this.onEvent,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Up
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(width: 88),
            _buildButton(label: '\u25B2', event: 'nav_up'),
            const SizedBox(width: 88),
          ],
        ),
        const SizedBox(height: 8),
        // Left / OK / Right
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildButton(label: '\u25C0', event: 'nav_left'),
            const SizedBox(width: 8),
            _buildButton(label: 'OK', event: 'confirm', fontSize: 18),
            const SizedBox(width: 8),
            _buildButton(label: '\u25B6', event: 'nav_right'),
          ],
        ),
        const SizedBox(height: 8),
        // Down
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(width: 88),
            _buildButton(label: '\u25BC', event: 'nav_down'),
            const SizedBox(width: 88),
          ],
        ),
      ],
    );
  }

  Widget _buildButton({
    required String label,
    required String event,
    double fontSize = 24,
  }) {
    return SizedBox(
      width: 80,
      height: 68,
      child: OutlinedButton(
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: Colors.green, width: 2),
          foregroundColor: Colors.green,
          backgroundColor: const Color(0xFF1A1A1A),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: EdgeInsets.zero,
        ),
        onPressed: () {
          HapticFeedback.mediumImpact();
          onEvent(event);
        },
        child: Text(
          label,
          style: TextStyle(
            fontFamily: 'monospace',
            fontSize: fontSize,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
