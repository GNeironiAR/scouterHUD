import 'package:flutter/material.dart';

import '../services/websocket_service.dart';
import '../theme/scouter_colors.dart';
import '../widgets/numpad_widget.dart';

class NumpadScreen extends StatelessWidget {
  final WebSocketService wsService;
  final bool pinMode;

  const NumpadScreen({
    super.key,
    required this.wsService,
    this.pinMode = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // PIN banner (only in PIN mode)
        if (pinMode)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 5),
            decoration: BoxDecoration(
              color: ScouterColors.yellow.withValues(alpha: 0.15),
              border: Border(
                bottom: BorderSide(
                  color: ScouterColors.yellow.withValues(alpha: 0.3),
                ),
              ),
            ),
            child: const Text(
              'PIN ENTRY \u2014 Type digits, \u232B to delete, SEND to submit',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'monospace',
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: ScouterColors.yellow,
                letterSpacing: 1,
              ),
            ),
          ),
        // Numpad centered
        Expanded(
          child: Center(
            child: NumpadWidget(onEvent: wsService.sendEvent),
          ),
        ),
      ],
    );
  }
}
