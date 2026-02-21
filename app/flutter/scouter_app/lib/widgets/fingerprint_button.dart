import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:local_auth/local_auth.dart';

import '../theme/scouter_colors.dart';

class FingerprintButton extends StatefulWidget {
  final void Function(bool success) onResult;

  const FingerprintButton({super.key, required this.onResult});

  @override
  State<FingerprintButton> createState() => _FingerprintButtonState();
}

enum _BiometricStatus { checking, available, unavailable }

enum _AuthFeedback { none, authenticating, success, failed }

class _FingerprintButtonState extends State<FingerprintButton> {
  final LocalAuthentication _localAuth = LocalAuthentication();
  _BiometricStatus _status = _BiometricStatus.checking;
  _AuthFeedback _feedback = _AuthFeedback.none;

  @override
  void initState() {
    super.initState();
    _checkBiometrics();
  }

  Future<void> _checkBiometrics() async {
    try {
      final isSupported = await _localAuth.isDeviceSupported();
      final canCheck = await _localAuth.canCheckBiometrics;
      if (mounted) {
        setState(() {
          _status = (isSupported && canCheck)
              ? _BiometricStatus.available
              : _BiometricStatus.unavailable;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _status = _BiometricStatus.unavailable);
      }
    }
  }

  Future<void> _authenticate() async {
    if (_feedback == _AuthFeedback.authenticating) return;

    setState(() => _feedback = _AuthFeedback.authenticating);
    HapticFeedback.heavyImpact();

    try {
      final success = await _localAuth.authenticate(
        localizedReason: 'Authenticate to ScouterHUD',
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: false,
        ),
      );

      if (!mounted) return;

      setState(() {
        _feedback = success ? _AuthFeedback.success : _AuthFeedback.failed;
      });

      widget.onResult(success);

      // Reset feedback after brief flash
      await Future.delayed(const Duration(milliseconds: 600));
      if (mounted) setState(() => _feedback = _AuthFeedback.none);
    } catch (_) {
      if (!mounted) return;
      setState(() => _feedback = _AuthFeedback.failed);
      widget.onResult(false);
      await Future.delayed(const Duration(milliseconds: 600));
      if (mounted) setState(() => _feedback = _AuthFeedback.none);
    }
  }

  Color get _borderColor {
    if (_status == _BiometricStatus.unavailable) return ScouterColors.gray;
    return switch (_feedback) {
      _AuthFeedback.success => ScouterColors.green,
      _AuthFeedback.failed => ScouterColors.red,
      _AuthFeedback.authenticating => ScouterColors.yellow,
      _AuthFeedback.none => ScouterColors.cyan,
    };
  }

  Color get _iconColor {
    if (_status == _BiometricStatus.unavailable) return ScouterColors.gray;
    return switch (_feedback) {
      _AuthFeedback.success => ScouterColors.green,
      _AuthFeedback.failed => ScouterColors.red,
      _AuthFeedback.authenticating => ScouterColors.yellow,
      _AuthFeedback.none => ScouterColors.cyan,
    };
  }

  @override
  Widget build(BuildContext context) {
    final isAvailable = _status == _BiometricStatus.available;
    final isChecking = _status == _BiometricStatus.checking;
    final isAuthenticating = _feedback == _AuthFeedback.authenticating;

    return Center(
      child: SizedBox(
        width: 88,
        height: 180,
        child: OutlinedButton(
          style: OutlinedButton.styleFrom(
            side: BorderSide(color: _borderColor, width: 2),
            foregroundColor: _iconColor,
            backgroundColor: ScouterColors.surface,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            padding: EdgeInsets.zero,
          ),
          onPressed: (isAvailable && !isAuthenticating) ? _authenticate : null,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (isAuthenticating)
                SizedBox(
                  width: 48,
                  height: 48,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: _iconColor,
                  ),
                )
              else
                Icon(
                  Icons.fingerprint,
                  size: 48,
                  color: _iconColor,
                ),
              const SizedBox(height: 8),
              Text(
                isChecking
                    ? '...'
                    : isAvailable
                        ? 'AUTH'
                        : 'N/A',
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2,
                  color: _iconColor,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
