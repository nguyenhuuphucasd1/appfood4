import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../models/dish.dart';
import 'dish_image.dart';

class FoodCard extends StatelessWidget {
  const FoodCard({
    super.key,
    required this.dish,
    required this.onTap,
    this.onFavorite,
  });

  final Dish dish;
  final VoidCallback onTap;
  final VoidCallback? onFavorite;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 210,
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    DishImage(name: dish.name, imageUrl: dish.imageUrl),
                    Positioned(
                      top: 10,
                      right: 10,
                      child: CircleAvatar(
                        radius: 17,
                        backgroundColor: Colors.white.withValues(alpha: .92),
                        child: IconButton(
                          onPressed: onFavorite,
                          tooltip: dish.isFavorite
                              ? 'Bỏ yêu thích'
                              : 'Thêm vào yêu thích',
                          icon: Icon(
                            dish.isFavorite
                                ? Icons.favorite_rounded
                                : Icons.favorite_border_rounded,
                            size: 19,
                            color: AppColors.orange,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      dish.name,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Icon(
                          dish.hasRecipe
                              ? Icons.menu_book_rounded
                              : Icons.info_outline_rounded,
                          size: 17,
                          color: dish.hasRecipe
                              ? AppColors.forest
                              : AppColors.muted,
                        ),
                        const SizedBox(width: 3),
                        Expanded(
                          child: Text(
                            dish.hasRecipe
                                ? 'Có công thức'
                                : 'Chưa có công thức đã kiểm chứng',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ),
                        const SizedBox(width: 5),
                        const Icon(
                          Icons.schedule_rounded,
                          size: 15,
                          color: AppColors.muted,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          dish.totalMinutes == null
                              ? 'Chưa rõ'
                              : '${dish.totalMinutes} phút',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
