import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'models/hud_state.dart';
import 'screens/control_screen.dart';
import 'services/websocket_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.landscapeLeft,
    DeviceOrientation.landscapeRight,
  ]);
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  runApp(const ScouterApp());
}

class ScouterApp extends StatefulWidget {
  const ScouterApp({super.key});

  @override
  State<ScouterApp> createState() => _ScouterAppState();
}

class _ScouterAppState extends State<ScouterApp> {
  final HudConnection _hudConnection = HudConnection();
  late final WebSocketService _wsService;

  @override
  void initState() {
    super.initState();
    _wsService = WebSocketService(_hudConnection);
    _autoConnect();
  }

  Future<void> _autoConnect() async {
    final prefs = await SharedPreferences.getInstance();
    final lastHost = prefs.getString('hud_host');
    if (lastHost != null) {
      final parts = lastHost.split(':');
      final host = parts[0];
      final port = parts.length > 1 ? int.tryParse(parts[1]) ?? 8765 : 8765;
      _wsService.connect(host, port);
    }
  }

  @override
  void dispose() {
    _wsService.disconnect();
    _hudConnection.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider.value(
      value: _hudConnection,
      child: MaterialApp(
        title: 'ScouterApp',
        debugShowCheckedModeBanner: false,
        theme: ThemeData.dark().copyWith(
          scaffoldBackgroundColor: const Color(0xFF111111),
        ),
        home: _AppHome(wsService: _wsService),
      ),
    );
  }
}

class _AppHome extends StatelessWidget {
  final WebSocketService wsService;

  const _AppHome({required this.wsService});

  @override
  Widget build(BuildContext context) {
    return Consumer<HudConnection>(
      builder: (context, hud, _) {
        if (!hud.isConnected) {
          return _ConnectScreen(wsService: wsService);
        }
        return ControlScreen(wsService: wsService);
      },
    );
  }
}

class _ConnectScreen extends StatefulWidget {
  final WebSocketService wsService;

  const _ConnectScreen({required this.wsService});

  @override
  State<_ConnectScreen> createState() => _ConnectScreenState();
}

class _ConnectScreenState extends State<_ConnectScreen> {
  final _controller = TextEditingController();
  bool _connecting = false;

  @override
  void initState() {
    super.initState();
    _loadSavedHost();
  }

  Future<void> _loadSavedHost() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('hud_host');
    if (saved != null) {
      _controller.text = saved;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF111111),
      body: Center(
        child: SizedBox(
          width: 400,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                'SCOUTERAPP',
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Colors.green,
                  letterSpacing: 4,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Connect to ScouterHUD',
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 14,
                  color: Color(0xFF00AA00),
                ),
              ),
              const SizedBox(height: 32),
              TextField(
                controller: _controller,
                style: const TextStyle(
                  color: Colors.green,
                  fontFamily: 'monospace',
                  fontSize: 16,
                ),
                decoration: const InputDecoration(
                  hintText: '192.168.1.87:8765',
                  hintStyle: TextStyle(color: Color(0xFF555555)),
                  labelText: 'HUD Address (IP:Port)',
                  labelStyle: TextStyle(color: Color(0xFF00AA00)),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.green),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.green, width: 2),
                  ),
                ),
                keyboardType: TextInputType.url,
                onSubmitted: (_) => _connect(),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.green, width: 2),
                    foregroundColor: Colors.green,
                    backgroundColor: const Color(0xFF1A1A1A),
                  ),
                  onPressed: _connecting ? null : _connect,
                  child: Text(
                    _connecting ? 'CONNECTING...' : 'CONNECT',
                    style: const TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                    ),
                  ),
                ),
              ),
              // Connection error display
              Consumer<HudConnection>(
                builder: (context, hud, _) {
                  final err = hud.connectionError;
                  if (err == null || err.isEmpty) {
                    return const SizedBox.shrink();
                  }
                  return Padding(
                    padding: const EdgeInsets.only(top: 16),
                    child: Text(
                      err,
                      textAlign: TextAlign.center,
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.red,
                        fontFamily: 'monospace',
                        fontSize: 11,
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _connect() async {
    final input = _controller.text.trim();
    if (input.isEmpty) return;

    setState(() => _connecting = true);

    final parts = input.split(':');
    final host = parts[0];
    final port = parts.length > 1 ? int.tryParse(parts[1]) ?? 8765 : 8765;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('hud_host', input);

    widget.wsService.connect(host, port);

    await Future.delayed(const Duration(seconds: 2));
    if (mounted) setState(() => _connecting = false);
  }
}
