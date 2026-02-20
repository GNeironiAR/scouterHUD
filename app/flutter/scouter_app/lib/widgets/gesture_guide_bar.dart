import 'package:flutter/material.dart';

import '../models/panel_state.dart';
import '../theme/scouter_colors.dart';

class GestureGuideBar extends StatelessWidget {
  final PanelState activePanel;

  const GestureGuideBar({super.key, required this.activePanel});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: const BoxDecoration(
        color: ScouterColors.surface,
        border: Border(top: BorderSide(color: ScouterColors.border)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _hint(
            '\u25C1 NUMPAD',
            activePanel == PanelState.numpad
                ? ScouterColors.yellow
                : ScouterColors.textDim,
          ),
          _hint(
            'ALPHA \u25B7',
            activePanel == PanelState.alpha
                ? ScouterColors.cyan
                : ScouterColors.textDim,
          ),
        ],
      ),
    );
  }

  Widget _hint(String text, Color color) {
    return Text(
      text,
      style: TextStyle(
        fontFamily: 'monospace',
        fontSize: 9,
        color: color,
        letterSpacing: 1,
      ),
    );
  }
}
