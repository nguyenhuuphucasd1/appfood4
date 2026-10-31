import 'package:flutter/material.dart';

import '../models/dish.dart';
import '../services/api_client.dart';
import '../state/app_state.dart';
import '../theme/app_theme.dart';
import '../widgets/dish_image.dart';
import 'login_screen.dart';
import 'recipe_detail_screen.dart';

class FavoritesScreen extends StatefulWidget {
  const FavoritesScreen({super.key});

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  bool _requested = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final state = AppStateScope.of(context);
    if (!_requested && state.isAuthenticated) {
      _requested = true;
      WidgetsBinding.instance.addPostFrameCallback(
        (_) => state.loadFavorites(),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppStateScope.of(context);
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 18, 20, 0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Món yêu thích',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 6),
            Text(
              'Danh sách được đồng bộ theo tài khoản.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 18),
            Expanded(
              child: !state.isAuthenticated
                  ? _GuestState(
                      onLogin: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const LoginScreen()),
                      ),
                    )
                  : state.favoritesLoading && state.favorites.isEmpty
                  ? const Center(child: CircularProgressIndicator())
                  : state.favorites.isEmpty
                  ? const _EmptyState()
                  : RefreshIndicator(
                      onRefresh: state.loadFavorites,
                      child: LayoutBuilder(
                        builder: (context, constraints) {
                          final columns = constraints.maxWidth >= 850
                              ? 3
                              : constraints.maxWidth >= 560
                              ? 2
                              : 1;
                          return GridView.builder(
                            gridDelegate:
                                SliverGridDelegateWithFixedCrossAxisCount(
                                  crossAxisCount: columns,
                                  mainAxisSpacing: 12,
                                  crossAxisSpacing: 12,
                                  childAspectRatio: columns == 1 ? 2.5 : 1.5,
                                ),
                            itemCount: state.favorites.length,
                            itemBuilder: (context, index) => _FavoriteCard(
                              dish: state.favorites[index],
                              onOpen: () => Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => RecipeDetailScreen(
                                    dish: state.favorites[index],
                                  ),
                                ),
                              ),
                              onRemove: () => _remove(state.favorites[index]),
                            ),
                          );
                        },
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _remove(Dish dish) async {
    try {
      await AppStateScope.of(context).toggleFavorite(dish);
    } on ApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.message)));
      }
    }
  }
}

class _FavoriteCard extends StatelessWidget {
  const _FavoriteCard({
    required this.dish,
    required this.onOpen,
    required this.onRemove,
  });
  final Dish dish;
  final VoidCallback onOpen;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) => Card(
    clipBehavior: Clip.antiAlias,
    child: InkWell(
      onTap: onOpen,
      child: Row(
        children: [
          SizedBox(
            width: 130,
            height: double.infinity,
            child: DishImage(name: dish.name, imageUrl: dish.imageUrl),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    dish.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    dish.hasRecipe
                        ? 'Có công thức kèm nguồn'
                        : 'Chưa có công thức đã kiểm chứng',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          ),
          IconButton(
            onPressed: onRemove,
            tooltip: 'Bỏ yêu thích',
            icon: const Icon(Icons.favorite_rounded, color: AppColors.orange),
          ),
          const SizedBox(width: 6),
        ],
      ),
    ),
  );
}

class _GuestState extends StatelessWidget {
  const _GuestState({required this.onLogin});
  final VoidCallback onLogin;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(
          Icons.lock_outline_rounded,
          size: 58,
          color: AppColors.muted,
        ),
        const SizedBox(height: 14),
        Text(
          'Đăng nhập để đồng bộ yêu thích',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        FilledButton(onPressed: onLogin, child: const Text('Đăng nhập')),
      ],
    ),
  );
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(
          Icons.favorite_outline_rounded,
          size: 58,
          color: AppColors.orange,
        ),
        const SizedBox(height: 14),
        Text(
          'Chưa có món được lưu',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 8),
        const Text('Chạm biểu tượng trái tim ở món bạn yêu thích.'),
      ],
    ),
  );
}
