import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models/hud_state.dart';
import '../services/websocket_service.dart';
import '../theme/scouter_colors.dart';

class DeviceListScreen extends StatelessWidget {
  final WebSocketService wsService;

  const DeviceListScreen({super.key, required this.wsService});

  @override
  Widget build(BuildContext context) {
    return Consumer<HudConnection>(
      builder: (context, hud, _) {
        final devices = hud.deviceList;
        final selected = hud.deviceListSelected;
        final activeId = hud.activeDeviceId;

        return Column(
          children: [
            // Header with BACK button
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: const BoxDecoration(
                color: ScouterColors.surface,
                border:
                    Border(bottom: BorderSide(color: ScouterColors.border)),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.devices,
                    color: ScouterColors.blue,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'DEVICES',
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: ScouterColors.blue,
                      letterSpacing: 2,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '(${devices.length})',
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 14,
                      color: ScouterColors.textDim,
                    ),
                  ),
                  const Spacer(),
                  SizedBox(
                    height: 36,
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(
                            color: ScouterColors.red, width: 2),
                        foregroundColor: ScouterColors.red,
                        backgroundColor: ScouterColors.surface,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                      ),
                      onPressed: () {
                        HapticFeedback.lightImpact();
                        wsService.sendEvent('cancel');
                      },
                      child: const Text(
                        '\u2715 BACK',
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            // Device list
            Expanded(
              child: devices.isEmpty
                  ? _buildEmptyState()
                  : _buildDeviceList(context, devices, selected, activeId),
            ),
            // Bottom bar with CONNECT button
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: const BoxDecoration(
                color: ScouterColors.surface,
                border: Border(top: BorderSide(color: ScouterColors.border)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    height: 40,
                    width: 160,
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(
                            color: ScouterColors.green, width: 2),
                        foregroundColor: ScouterColors.green,
                        backgroundColor: ScouterColors.surface,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      onPressed: devices.isEmpty
                          ? null
                          : () {
                              HapticFeedback.mediumImpact();
                              wsService.sendEvent('confirm');
                            },
                      child: const Text(
                        'CONNECT',
                        style: TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildEmptyState() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.device_unknown,
            size: 48,
            color: ScouterColors.gray,
          ),
          SizedBox(height: 12),
          Text(
            'No devices yet',
            style: TextStyle(
              fontFamily: 'monospace',
              fontSize: 14,
              color: ScouterColors.textDim,
            ),
          ),
          SizedBox(height: 4),
          Text(
            'Scan a QR to connect',
            style: TextStyle(
              fontFamily: 'monospace',
              fontSize: 12,
              color: ScouterColors.gray,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDeviceList(
    BuildContext context,
    List<DeviceInfo> devices,
    int selected,
    String activeId,
  ) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: devices.length,
      itemBuilder: (context, index) {
        final device = devices[index];
        final isSelected = index == selected;
        final isActive = device.id == activeId;

        return GestureDetector(
          onTap: () {
            HapticFeedback.selectionClick();
            if (isSelected) {
              // Tap on already selected → connect
              wsService.sendEvent('confirm');
            } else {
              // Navigate to this device by sending nav events
              final diff = index - selected;
              final event = diff > 0 ? 'nav_down' : 'nav_up';
              for (var i = 0; i < diff.abs(); i++) {
                wsService.sendEvent(event);
              }
            }
          },
          child: Container(
            margin: const EdgeInsets.only(bottom: 4),
            padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: isSelected
                  ? ScouterColors.blue.withValues(alpha: 0.15)
                  : ScouterColors.background,
              border: Border.all(
                color: isSelected ? ScouterColors.blue : ScouterColors.border,
                width: isSelected ? 2 : 1,
              ),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                // Selection indicator
                Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.only(right: 10),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color:
                        isSelected ? ScouterColors.blue : Colors.transparent,
                  ),
                ),
                // Device info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              device.name.isNotEmpty
                                  ? device.name
                                  : device.id,
                              style: TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                                color: isSelected
                                    ? ScouterColors.blue
                                    : ScouterColors.textPrimary,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          if (isActive)
                            Container(
                              margin: const EdgeInsets.only(left: 8),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 6,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: ScouterColors.green
                                    .withValues(alpha: 0.2),
                                border: Border.all(
                                  color: ScouterColors.green
                                      .withValues(alpha: 0.5),
                                ),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text(
                                'ACTIVE',
                                style: TextStyle(
                                  fontFamily: 'monospace',
                                  fontSize: 9,
                                  fontWeight: FontWeight.bold,
                                  color: ScouterColors.green,
                                ),
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          Text(
                            device.type,
                            style: const TextStyle(
                              fontFamily: 'monospace',
                              fontSize: 11,
                              color: ScouterColors.textDim,
                            ),
                          ),
                          if (device.auth != 'open') ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 4,
                                vertical: 1,
                              ),
                              decoration: BoxDecoration(
                                border:
                                    Border.all(color: ScouterColors.yellow),
                                borderRadius: BorderRadius.circular(3),
                              ),
                              child: Text(
                                device.auth.toUpperCase(),
                                style: const TextStyle(
                                  fontFamily: 'monospace',
                                  fontSize: 9,
                                  fontWeight: FontWeight.bold,
                                  color: ScouterColors.yellow,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
