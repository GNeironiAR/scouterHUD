import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/scouter_colors.dart';

class FingerprintButton extends StatelessWidget {
  final VoidCallback onPressed;

  const FingerprintButton({super.key, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SizedBox(
        width: 88,
        height: 180,
        child: OutlinedButton(
          style: OutlinedButton.styleFrom(
            side: const BorderSide(color: ScouterColors.cyan, width: 2),
            foregroundColor: ScouterColors.cyan,
            backgroundColor: ScouterColors.surface,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            padding: EdgeInsets.zero,
          ),
          onPressed: () {
            HapticFeedback.heavyImpact();
            onPressed();
          },
          child: const Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.fingerprint,
                size: 48,
                color: ScouterColors.cyan,
              ),
              SizedBox(height: 8),
              Text(
                'AUTH',
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
