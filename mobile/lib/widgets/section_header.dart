import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class SectionHeader extends StatelessWidget {
  const SectionHeader({
    super.key,
    required this.title,
    this.action = 'Xem tất cả',
    this.onPressed,
  });
  final String title;
  final String action;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Text(title, style: Theme.of(context).textTheme.titleLarge),
        ),
        if (onPressed != null)
          TextButton.icon(
            onPressed: onPressed,
            iconAlignment: IconAlignment.end,
            icon: const Icon(Icons.arrow_forward_rounded, size: 16),
            label: Text(action),
            style: TextButton.styleFrom(foregroundColor: AppColors.forest),
          ),
      ],
    );
  }
}
