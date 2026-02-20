import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/hud_state.dart';
import '../models/panel_state.dart';
import '../theme/scouter_colors.dart';

class StatusBarWidget extends StatelessWidget {
  const StatusBarWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<HudConnection>(
      builder: (context, hud, _) {
        final connected = hud.isConnected;

        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: const BoxDecoration(
            color: ScouterColors.surface,
            border: Border(bottom: BorderSide(color: ScouterColors.border)),
          ),
          child: Row(
            children: [
              // Left: connection status
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: connected ? ScouterColors.green : ScouterColors.red,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                connected ? 'CONNECTED' : 'DISCONNECTED',
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: connected ? ScouterColors.green : ScouterColors.red,
                ),
              ),
              const Spacer(),
              // Center: app name + device
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'SCOUTERAPP',
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: ScouterColors.textPrimary,
                      letterSpacing: 2,
                    ),
                  ),
                  if (hud.deviceName != null && hud.state == HudState.streaming)
                    Text(
                      hud.deviceName!,
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 10,
                        color: ScouterColors.textDim,
                      ),
                    ),
                ],
              ),
              const Spacer(),
              // Right: current mode
              Text(
                _modeLabel(hud.activePanel),
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: _modeColor(hud.activePanel),
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  String _modeLabel(PanelState panel) {
    switch (panel) {
      case PanelState.base:
        return 'REMOTE';
      case PanelState.numpad:
        return 'NUMPAD';
      case PanelState.alpha:
        return 'KEYBOARD';
      case PanelState.aiChat:
        return 'AI CHAT';
    }
  }

  Color _modeColor(PanelState panel) {
    switch (panel) {
      case PanelState.base:
        return ScouterColors.green;
      case PanelState.numpad:
        return ScouterColors.yellow;
      case PanelState.alpha:
        return ScouterColors.cyan;
      case PanelState.aiChat:
        return ScouterColors.purple;
    }
  }
}
