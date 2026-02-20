import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/scouter_colors.dart';

class AiChatButton extends StatelessWidget {
  final VoidCallback onPressed;

  const AiChatButton({super.key, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 140,
      height: 44,
      child: OutlinedButton.icon(
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: ScouterColors.purple, width: 2),
          foregroundColor: ScouterColors.purple,
          backgroundColor: ScouterColors.surface,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: EdgeInsets.zero,
        ),
        onPressed: () {
          HapticFeedback.mediumImpact();
          onPressed();
        },
        icon: const Text(
          '\u25C6',
          style: TextStyle(fontSize: 14),
        ),
        label: const Text(
          'AI CHAT',
          style: TextStyle(
            fontFamily: 'monospace',
            fontSize: 13,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
