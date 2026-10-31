import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import 'ai_camera_screen.dart';
import 'discover_screen.dart';
import 'favorites_screen.dart';
import 'home_screen.dart';
import 'profile_screen.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;

  late final List<Widget> _pages = [
    HomeScreen(onOpenDiscover: () => setState(() => _index = 1)),
    const DiscoverScreen(),
    const AiCameraScreen(),
    const FavoritesScreen(),
    const ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 900;
    final navigation = NavigationBar(
      selectedIndex: _index,
      onDestinationSelected: (value) => setState(() => _index = value),
      indicatorColor: AppColors.forest.withValues(alpha: .13),
      backgroundColor: Colors.white,
      height: 72,
      destinations: const [
        NavigationDestination(
          icon: Icon(Icons.home_outlined),
          selectedIcon: Icon(Icons.home_rounded),
          label: 'Trang chủ',
        ),
        NavigationDestination(
          icon: Icon(Icons.grid_view_rounded),
          label: 'Công thức',
        ),
        NavigationDestination(
          icon: Icon(Icons.camera_alt_outlined),
          selectedIcon: Icon(Icons.camera_alt_rounded),
          label: 'Máy ảnh',
        ),
        NavigationDestination(
          icon: Icon(Icons.favorite_outline_rounded),
          selectedIcon: Icon(Icons.favorite_rounded),
          label: 'Yêu thích',
        ),
        NavigationDestination(
          icon: Icon(Icons.person_outline_rounded),
          selectedIcon: Icon(Icons.person_rounded),
          label: 'Cá nhân',
        ),
      ],
    );
    if (!wide) {
      return Scaffold(
        body: IndexedStack(index: _index, children: _pages),
        bottomNavigationBar: navigation,
      );
    }
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _index,
            onDestinationSelected: (value) => setState(() => _index = value),
            labelType: NavigationRailLabelType.all,
            backgroundColor: Colors.white,
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.home_outlined),
                selectedIcon: Icon(Icons.home),
                label: Text('Trang chủ'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.grid_view_rounded),
                label: Text('Công thức'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.camera_alt_outlined),
                selectedIcon: Icon(Icons.camera_alt),
                label: Text('Máy ảnh'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.favorite_outline),
                selectedIcon: Icon(Icons.favorite),
                label: Text('Yêu thích'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.person_outline),
                selectedIcon: Icon(Icons.person),
                label: Text('Cá nhân'),
              ),
            ],
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1180),
                child: IndexedStack(index: _index, children: _pages),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
