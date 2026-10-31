import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../services/api_client.dart';

class DishImage extends StatelessWidget {
  const DishImage({
    super.key,
    required this.name,
    this.imageUrl,
    this.fit = BoxFit.cover,
  });
  final String name;
  final String? imageUrl;
  final BoxFit fit;

  @override
  Widget build(BuildContext context) {
    final url = imageUrl?.trim();
    if (url != null && url.isNotEmpty) {
      return Semantics(
        image: true,
        label: 'Ảnh món $name',
        child: Image.network(
          ApiConfig.resolveUrl(url),
          fit: fit,
          errorBuilder: (_, _, _) => _placeholder(),
        ),
      );
    }
    return _placeholder();
  }

  Widget _placeholder() => ColoredBox(
    color: AppColors.creamStrong,
    child: Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.restaurant_menu_rounded,
            color: AppColors.forest,
            size: 42,
          ),
          const SizedBox(height: 7),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: Text(
              name,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: AppColors.forestDark,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    ),
  );
}
