import 'package:flutter/material.dart';

class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.compact = false, this.light = false});

  final bool compact;
  final bool light;

  @override
  Widget build(BuildContext context) {
    final logo = Semantics(
      label: 'Logo Vị Việt',
      image: true,
      child: Image.asset(
        'assets/images/vi_viet_logo_full.png',
        width: compact ? 142 : 220,
        height: compact ? 52 : 80,
        fit: BoxFit.contain,
        filterQuality: FilterQuality.high,
        excludeFromSemantics: true,
      ),
    );

    if (!light) return logo;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: .94),
        borderRadius: BorderRadius.circular(compact ? 14 : 18),
      ),
      child: Padding(
        padding: EdgeInsets.symmetric(
          horizontal: compact ? 10 : 14,
          vertical: compact ? 7 : 9,
        ),
        child: logo,
      ),
    );
  }
}
