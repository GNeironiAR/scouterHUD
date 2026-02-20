import 'package:flutter/material.dart';

import '../services/websocket_service.dart';
import '../widgets/alpha_keyboard_widget.dart';

class AlphaKeyboardScreen extends StatelessWidget {
  final WebSocketService wsService;

  const AlphaKeyboardScreen({
    super.key,
    required this.wsService,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(
        left: 40, // left safe zone (camera)
        right: 48, // right safe zone
        top: 8,
        bottom: 8,
      ),
      child: AlphaKeyboardWidget(
        onEvent: (eventName, {String? value}) {
          wsService.sendAlphaKey(eventName, value: value);
        },
      ),
    );
  }
}
