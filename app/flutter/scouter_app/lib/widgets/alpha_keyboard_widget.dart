import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/scouter_colors.dart';

class AlphaKeyboardWidget extends StatefulWidget {
  final void Function(String eventName, {String? value}) onEvent;

  const AlphaKeyboardWidget({super.key, required this.onEvent});

  @override
  State<AlphaKeyboardWidget> createState() => _AlphaKeyboardWidgetState();
}

class _AlphaKeyboardWidgetState extends State<AlphaKeyboardWidget> {
  bool _shift = false;

  static const _row1 = ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'];
  static const _row2 = ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'];
  static const _row3 = ['Z', 'X', 'C', 'V', 'B', 'N', 'M'];

  void _onKey(String char) {
    HapticFeedback.lightImpact();
    final value = _shift ? char.toUpperCase() : char.toLowerCase();
    widget.onEvent('alpha_key', value: value);
    if (_shift) {
      setState(() => _shift = false);
    }
  }

  void _onBackspace() {
    HapticFeedback.mediumImpact();
    widget.onEvent('alpha_backspace');
  }

  void _onSpace() {
    HapticFeedback.lightImpact();
    widget.onEvent('alpha_key', value: ' ');
  }

  void _onEnter() {
    HapticFeedback.mediumImpact();
    widget.onEvent('alpha_enter');
  }

  void _onShift() {
    HapticFeedback.lightImpact();
    setState(() => _shift = !_shift);
    widget.onEvent('alpha_shift');
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // Left column: SPACE (tall) + SHIFT
        SizedBox(
          width: 80,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Expanded(
                flex: 3,
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: _sideButton(
                    'SPC',
                    ScouterColors.cyan,
                    _onSpace,
                  ),
                ),
              ),
              Expanded(
                child: _sideButton(
                  _shift ? '\u21E7' : '\u21E7',
                  _shift ? ScouterColors.green : ScouterColors.gray,
                  _onShift,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 6),
        // Center: QWERTY rows (expanded to fill)
        Expanded(
          child: Column(
            children: [
              Expanded(child: _buildKeyRow(_row1)),
              const SizedBox(height: 4),
              Expanded(child: _buildKeyRow(_row2)),
              const SizedBox(height: 4),
              Expanded(child: _buildKeyRowWithBackspace(_row3)),
            ],
          ),
        ),
        const SizedBox(width: 6),
        // Right column: ENTER (tall)
        SizedBox(
          width: 80,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Expanded(
                child: _sideButton(
                  'ENT\nER',
                  ScouterColors.green,
                  _onEnter,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildKeyRow(List<String> keys) {
    return Row(
      children: keys.map((key) {
        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 1.5),
            child: _letterKey(key),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildKeyRowWithBackspace(List<String> keys) {
    return Row(
      children: [
        ...keys.map((key) {
          return Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 1.5),
              child: _letterKey(key),
            ),
          );
        }),
        Expanded(
          flex: 2,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 1.5),
            child: SizedBox.expand(
              child: OutlinedButton(
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: ScouterColors.red, width: 1.5),
                  foregroundColor: ScouterColors.red,
                  backgroundColor: ScouterColors.surface,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(6),
                  ),
                  padding: EdgeInsets.zero,
                ),
                onPressed: _onBackspace,
                child: const Text(
                  '\u232B',
                  style: TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _letterKey(String letter) {
    final display = _shift ? letter.toUpperCase() : letter.toLowerCase();
    return SizedBox.expand(
      child: OutlinedButton(
        style: OutlinedButton.styleFrom(
          side: BorderSide(
            color: ScouterColors.cyan.withValues(alpha: 0.6),
            width: 1.5,
          ),
          foregroundColor: ScouterColors.textPrimary,
          backgroundColor: ScouterColors.surface,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(6),
          ),
          padding: EdgeInsets.zero,
        ),
        onPressed: () => _onKey(letter),
        child: Text(
          display,
          style: const TextStyle(
            fontFamily: 'monospace',
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _sideButton(String label, Color color, VoidCallback onPressed) {
    return SizedBox.expand(
      child: OutlinedButton(
        style: OutlinedButton.styleFrom(
          side: BorderSide(color: color, width: 2),
          foregroundColor: color,
          backgroundColor: ScouterColors.surface,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          padding: EdgeInsets.zero,
        ),
        onPressed: onPressed,
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontFamily: 'monospace',
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
