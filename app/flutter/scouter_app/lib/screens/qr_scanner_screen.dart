import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class QrScannerScreen extends StatefulWidget {
  final void Function(String url) onQrLinkDetected;

  const QrScannerScreen({super.key, required this.onQrLinkDetected});

  @override
  State<QrScannerScreen> createState() => _QrScannerScreenState();
}

class _QrScannerScreenState extends State<QrScannerScreen> {
  final MobileScannerController _controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
  );
  bool _detected = false;
  String _statusText = 'Point camera at a QR-Link code';
  Color _statusColor = Colors.yellow;
  int _scanCount = 0;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera preview
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
            errorBuilder: (context, error, child) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                    'Camera error: ${error.errorDetails?.message ?? error.errorCode.name}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      color: Colors.red,
                      fontFamily: 'monospace',
                      fontSize: 14,
                    ),
                  ),
                ),
              );
            },
          ),
          // Top bar
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.all(12),
              color: Colors.black54,
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.green),
                    onPressed: () => Navigator.pop(context),
                  ),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Scan QR-Link Code',
                      style: TextStyle(
                        color: Colors.yellow,
                        fontFamily: 'monospace',
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.flash_on, color: Colors.yellow),
                    onPressed: () => _controller.toggleTorch(),
                  ),
                ],
              ),
            ),
          ),
          // Bottom status bar — shows what's detected
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: Colors.black87,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (_detected)
                    const Icon(Icons.check_circle, color: Colors.green, size: 36),
                  const SizedBox(height: 4),
                  Text(
                    _statusText,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: _statusColor,
                      fontFamily: 'monospace',
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Scans: $_scanCount',
                    style: const TextStyle(
                      color: Color(0xFF555555),
                      fontFamily: 'monospace',
                      fontSize: 10,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _onDetect(BarcodeCapture capture) {
    if (_detected) return;

    setState(() => _scanCount++);

    for (final barcode in capture.barcodes) {
      // Try rawValue first, fall back to displayValue
      final value = barcode.rawValue ?? barcode.displayValue;

      if (value == null || value.isEmpty) {
        setState(() {
          _statusText = 'Detected barcode but value is empty (type: ${barcode.format.name})';
          _statusColor = Colors.orange;
        });
        continue;
      }

      if (value.startsWith('qrlink://')) {
        setState(() {
          _detected = true;
          _statusText = 'QR-Link detected! Sending...';
          _statusColor = Colors.green;
        });
        HapticFeedback.heavyImpact();
        widget.onQrLinkDetected(value);
        return;
      } else {
        setState(() {
          _statusText = 'Not a QR-Link:\n$value';
          _statusColor = Colors.red;
        });
      }
    }
  }
}
