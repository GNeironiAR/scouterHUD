import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class NumpadWidget extends StatelessWidget {
  final void Function(String eventName) onEvent;

  const NumpadWidget({super.key, required this.onEvent});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildRow(['1', '2', '3']),
        const SizedBox(height: 8),
        _buildRow(['4', '5', '6']),
        const SizedBox(height: 8),
        _buildRow(['7', '8', '9']),
        const SizedBox(height: 8),
        _buildRow(['\u232B', '0', 'SEND']),
      ],
    );
  }

  Widget _buildRow(List<String> labels) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: labels.map((label) {
        final isLast = label == labels.last;
        return Row(
          children: [
            _buildKey(label),
            if (!isLast) const SizedBox(width: 8),
          ],
        );
      }).toList(),
    );
  }

  Widget _buildKey(String label) {
    String event;
    Color color;
    double fontSize;

    if (label == 'SEND') {
      event = 'digit_submit';
      color = Colors.green;
      fontSize = 14;
    } else if (label == '\u232B') {
      event = 'digit_backspace';
      color = Colors.red;
      fontSize = 22;
    } else {
      event = 'digit_$label';
      color = Colors.yellow;
      fontSize = 22;
    }

    return SizedBox(
      width: 72,
      height: 56,
      child: OutlinedButton(
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: color, width: 2),
          foregroundColor: color,
          backgroundColor: const Color(0xFF16213E),
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
