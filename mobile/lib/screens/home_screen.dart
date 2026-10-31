import 'package:flutter/material.dart';

import '../models/dish.dart';
import '../services/api_client.dart';
import '../state/app_state.dart';
import '../theme/app_theme.dart';
import '../widgets/app_logo.dart';
import '../widgets/food_card.dart';
import '../widgets/section_header.dart';
import 'recipe_detail_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.onOpenDiscover});
  final VoidCallback onOpenDiscover;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _requested = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_requested) {
      _requested = true;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) AppStateScope.of(context).loadDishes();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppStateScope.of(context);
    final name = state.user?.fullName ?? 'Người yêu ẩm thực Việt';
    return SafeArea(
      child: RefreshIndicator(
        onRefresh: state.loadDishes,
        child: CustomScrollView(
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 0),
              sliver: SliverList.list(
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Xin chào,',
                              style: Theme.of(context).textTheme.bodyLarge
                                  ?.copyWith(color: AppColors.forest),
                            ),
                            Text(
                              '$name!',
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      const AppLogo(compact: true),
                    ],
                  ),
                  const SizedBox(height: 18),
                  Semantics(
                    button: true,
                    label: 'Mở tìm kiếm món ăn',
                    child: TextField(
                      readOnly: true,
                      onTap: widget.onOpenDiscover,
                      decoration: const InputDecoration(
                        prefixIcon: Icon(Icons.search_rounded),
                        hintText: 'Tìm món ăn, vùng miền...',
                        suffixIcon: Icon(Icons.tune_rounded),
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  _HeroBanner(onTap: widget.onOpenDiscover),
                  const SizedBox(height: 18),
                  SectionHeader(
                    title: 'Danh mục món Việt',
                    onPressed: widget.onOpenDiscover,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Danh mục được đồng bộ từ backend; công thức chỉ hiện khi có nguồn.',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 16),
                  SectionHeader(
                    title: 'Khám phá hôm nay',
                    onPressed: widget.onOpenDiscover,
                  ),
                  const SizedBox(height: 8),
                ],
              ),
            ),
            if (state.dishesLoading && state.dishes.isEmpty)
              const SliverToBoxAdapter(
                child: Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(child: CircularProgressIndicator()),
                ),
              )
            else if (state.dishes.isEmpty)
              SliverToBoxAdapter(
                child: _LoadError(
                  message: state.dishesError,
                  onRetry: state.loadDishes,
                ),
              )
            else
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 260,
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    scrollDirection: Axis.horizontal,
                    itemCount: state.dishes.length > 8
                        ? 8
                        : state.dishes.length,
                    separatorBuilder: (_, _) => const SizedBox(width: 14),
                    itemBuilder: (context, index) {
                      final dish = state.dishes[index];
                      return FoodCard(
                        dish: dish,
                        onTap: () => _openDetail(dish),
                        onFavorite: () => _toggleFavorite(dish),
                      );
                    },
                  ),
                ),
              ),
            const SliverToBoxAdapter(child: SizedBox(height: 24)),
          ],
        ),
      ),
    );
  }

  void _openDetail(Dish dish) {
    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => RecipeDetailScreen(dish: dish)));
  }

  Future<void> _toggleFavorite(Dish dish) async {
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

class _LoadError extends StatelessWidget {
  const _LoadError({required this.message, required this.onRetry});
  final String? message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(28),
    child: Column(
      children: [
        const Icon(Icons.cloud_off_rounded, size: 48, color: AppColors.muted),
        const SizedBox(height: 10),
        Text(message ?? 'Chưa có dữ liệu món ăn.', textAlign: TextAlign.center),
        TextButton.icon(
          onPressed: onRetry,
          icon: const Icon(Icons.refresh),
          label: const Text('Thử lại'),
        ),
      ],
    ),
  );
}

class _HeroBanner extends StatelessWidget {
  const _HeroBanner({required this.onTap});
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => SizedBox(
    height: 210,
    child: ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: Stack(
        fit: StackFit.expand,
        children: [
          Image.asset('assets/images/pho_hero.png', fit: BoxFit.cover),
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xD912241B), Color(0x3312241B)],
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(22),
            child: Align(
              alignment: Alignment.centerLeft,
              child: SizedBox(
                width: 230,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Nhận diện và khám phá món Việt',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 23,
                        height: 1.15,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Dữ liệu minh bạch, không bịa công thức',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: .86),
                      ),
                    ),
                    const SizedBox(height: 14),
                    FilledButton.tonalIcon(
                      onPressed: onTap,
                      iconAlignment: IconAlignment.end,
                      icon: const Icon(Icons.arrow_forward_rounded, size: 17),
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.amber,
                        foregroundColor: AppColors.forestDark,
                      ),
                      label: const Text('Khám phá ngay'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    ),
  );
}
