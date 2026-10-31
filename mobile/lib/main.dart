import 'package:flutter/material.dart';

import 'screens/splash_screen.dart';
import 'state/app_state.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ViVietApp());
}

class ViVietApp extends StatefulWidget {
  const ViVietApp({super.key, this.state});

  final AppState? state;

  @override
  State<ViVietApp> createState() => _ViVietAppState();
}

class _ViVietAppState extends State<ViVietApp> {
  late final AppState _state = widget.state ?? (AppState()..initialize());

  @override
  void dispose() {
    _state.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AppStateScope(
      state: _state,
      child: MaterialApp(
        title: 'Vị Việt',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        home: const SplashScreen(),
      ),
    );
  }
}
