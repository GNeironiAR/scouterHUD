import 'package:flutter/material.dart';

class EdgeHintWidget extends StatelessWidget {
  final String label;
  final Color color;
  final bool isLeft;

  const EdgeHintWidget({
    super.key,
    required this.label,
    required this.color,
    required this.isLeft,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 24,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 2,
            height: 60,
            color: color.withValues(alpha: 0.4),
          ),
          const SizedBox(height: 8),
          RotatedBox(
            quarterTurns: isLeft ? 3 : 1,
            child: Text(
              label,
              style: TextStyle(
                fontFamily: 'monospace',
                fontSize: 10,
                fontWeight: FontWeight.bold,
                color: color.withValues(alpha: 0.6),
                letterSpacing: 2,
              ),
            ),
          ),
          const SizedBox(height: 8),
          Container(
            width: 2,
            height: 60,
            color: color.withValues(alpha: 0.4),
          ),
        ],
      ),
    );
  }
}
