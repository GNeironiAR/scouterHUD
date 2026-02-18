import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/hud_state.dart';

class StatusBarWidget extends StatelessWidget {
  const StatusBarWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<HudConnection>(
      builder: (context, hud, _) {
        final connected = hud.isConnected;
        final stateText = _stateLabel(hud);

        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: const BoxDecoration(
            color: Color(0xFF1A1A1A),
            border: Border(bottom: BorderSide(color: Color(0xFF333333))),
          ),
          child: Row(
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: connected ? Colors.green : Colors.red,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                connected ? 'CONNECTED' : 'DISCONNECTED',
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 13,
                  color: connected ? Colors.green : Colors.red,
                ),
              ),
              const Spacer(),
              Text(
                stateText,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: Color(0xFF00AA00),
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  String _stateLabel(HudConnection hud) {
    final name = hud.state.name.toUpperCase();
    if (hud.deviceName != null && hud.state == HudState.streaming) {
      return '$name \u2014 ${hud.deviceName}';
    }
    return name;
  }
}
