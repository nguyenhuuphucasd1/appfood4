import 'dart:async';

import 'package:flutter/material.dart';

import '../models/dish.dart';
import '../services/api_client.dart';
import '../state/app_state.dart';
import '../theme/app_theme.dart';
import '../widgets/dish_image.dart';
import 'recipe_detail_screen.dart';

class DiscoverScreen extends StatefulWidget {
  const DiscoverScreen({super.key});

  @override
  State<DiscoverScreen> createState() => _DiscoverScreenState();
}

class _DiscoverScreenState extends State<DiscoverScreen> {
  final _search = TextEditingController();
  Timer? _debounce;
  String? _region;
  String? _category;
  String? _difficulty;
  int? _maxMinutes;
  bool _requested = false;

  bool get _hasFilters =>
      _region != null ||
      _category != null ||
      _difficulty != null ||
      _maxMinutes != null;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_requested) {
      _requested = true;
      final state = AppStateScope.of(context);
      if (state.dishes.isEmpty && !state.dishesLoading) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted && state.dishes.isEmpty && !state.dishesLoading) {
            state.loadDishes();
          }
        });
      }
    }
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    super.dispose();
  }

  void _searchChanged(String _) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 350), _load);
  }

  Future<void> _load() => AppStateScope.of(context).loadDishes(
    query: _search.text,
    region: _region,
    category: _category,
    difficulty: _difficulty,
    maxMinutes: _maxMinutes,
  );

  void _clearFilters() {
    setState(() {
      _region = null;
      _category = null;
      _difficulty = null;
      _maxMinutes = null;
    });
    _load();
  }

  Future<void> _showFilters() async {
    var region = _region;
    var category = _category;
    var difficulty = _difficulty;
    var maxMinutes = _maxMinutes;
    final applied = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) => SafeArea(
          child: Padding(
            padding: EdgeInsets.fromLTRB(
              20,
              20,
              20,
              20 + MediaQuery.viewInsetsOf(context).bottom,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Bộ lọc món ăn',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 16),
                _FilterDropdown(
                  label: 'Vùng miền',
                  value: region,
                  options: const ['Miền Bắc', 'Miền Trung', 'Miền Nam'],
                  onChanged: (value) => setSheetState(() => region = value),
                ),
                const SizedBox(height: 12),
                _FilterDropdown(
                  label: 'Danh mục',
                  value: category,
                  options: const [
                    'Món chính',
                    'Món chay',
                    'Món canh',
                    'Món ăn vặt',
                  ],
                  onChanged: (value) => setSheetState(() => category = value),
                ),
                const SizedBox(height: 12),
                _FilterDropdown(
                  label: 'Độ khó',
                  value: difficulty,
                  options: const ['Dễ', 'Trung bình', 'Khó'],
                  onChanged: (value) => setSheetState(() => difficulty = value),
                ),
                const SizedBox(height: 12),
                _FilterDropdown<int>(
                  label: 'Thời gian tối đa',
                  value: maxMinutes,
                  options: const [30, 60, 120],
                  labelFor: (value) => '$value phút',
                  onChanged: (value) => setSheetState(() => maxMinutes = value),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                          setSheetState(() {
                            region = null;
                            category = null;
                            difficulty = null;
                            maxMinutes = null;
                          });
                        },
                        child: const Text('Xóa bộ lọc'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: FilledButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: const Text('Áp dụng'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
    if (applied == true) {
      setState(() {
        _region = region;
        _category = category;
        _difficulty = difficulty;
        _maxMinutes = maxMinutes;
      });
      await _load();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppStateScope.of(context);
    final width = MediaQuery.sizeOf(context).width;
    final columns = width >= 1000
        ? 4
        : width >= 650
        ? 3
        : 2;
    return SafeArea(
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Khám phá món Việt',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 6),
                Text(
                  'Tìm kiếm không phân biệt dấu; dữ liệu lấy từ backend.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _search,
                  onChanged: _searchChanged,
                  textInputAction: TextInputAction.search,
                  onSubmitted: (_) => _load(),
                  decoration: InputDecoration(
                    prefixIcon: const Icon(Icons.search_rounded),
                    hintText: 'Tìm tên món ăn...',
                    suffixIcon: IconButton(
                      onPressed: _showFilters,
                      tooltip: 'Bộ lọc',
                      icon: Badge(
                        isLabelVisible: _hasFilters,
                        child: const Icon(Icons.tune_rounded),
                      ),
                    ),
                  ),
                ),
                if (_hasFilters)
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton.icon(
                      onPressed: _clearFilters,
                      icon: const Icon(Icons.close_rounded, size: 17),
                      label: const Text('Xóa bộ lọc'),
                    ),
                  ),
                if (state.dishesError != null && state.dishes.isNotEmpty)
                  Text(
                    'Đang hiển thị dữ liệu gần nhất: ${state.dishesError}',
                    style: const TextStyle(color: AppColors.orange),
                  ),
              ],
            ),
          ),
          Expanded(
            child: state.dishesLoading && state.dishes.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : state.dishes.isEmpty
                ? _NoResult(message: state.dishesError, onRetry: _load)
                : RefreshIndicator(
                    onRefresh: _load,
                    child: GridView.builder(
                      padding: const EdgeInsets.fromLTRB(20, 6, 20, 24),
                      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: columns,
                        crossAxisSpacing: 12,
                        mainAxisSpacing: 12,
                        childAspectRatio: .84,
                      ),
                      itemCount: state.dishes.length,
                      itemBuilder: (context, index) {
                        final dish = state.dishes[index];
                        return _DishTile(
                          dish: dish,
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => RecipeDetailScreen(dish: dish),
                            ),
                          ),
                          onFavorite: () => _toggleFavorite(dish),
                        );
                      },
                    ),
                  ),
          ),
        ],
      ),
    );
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

class _FilterDropdown<T> extends StatelessWidget {
  const _FilterDropdown({
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
    this.labelFor,
  });
  final String label;
  final T? value;
  final List<T> options;
  final ValueChanged<T?> onChanged;
  final String Function(T value)? labelFor;

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<T>(
    initialValue: value,
    decoration: InputDecoration(labelText: label),
    items: options
        .map(
          (value) => DropdownMenuItem(
            value: value,
            child: Text(labelFor?.call(value) ?? '$value'),
          ),
        )
        .toList(growable: false),
    onChanged: onChanged,
  );
}

class _DishTile extends StatelessWidget {
  const _DishTile({
    required this.dish,
    required this.onTap,
    required this.onFavorite,
  });
  final Dish dish;
  final VoidCallback onTap;
  final VoidCallback onFavorite;

  @override
  Widget build(BuildContext context) => Card(
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
                  top: 6,
                  right: 6,
                  child: IconButton.filledTonal(
                    onPressed: onFavorite,
                    tooltip: dish.isFavorite
                        ? 'Bỏ yêu thích'
                        : 'Thêm vào yêu thích',
                    icon: Icon(
                      dish.isFavorite
                          ? Icons.favorite_rounded
                          : Icons.favorite_border_rounded,
                    ),
                    color: AppColors.orange,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  dish.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  dish.hasRecipe
                      ? 'Có công thức kèm nguồn'
                      : 'Chưa có công thức đã kiểm chứng',
                  style: const TextStyle(color: AppColors.muted, fontSize: 11),
                ),
              ],
            ),
          ),
        ],
      ),
    ),
  );
}

class _NoResult extends StatelessWidget {
  const _NoResult({required this.message, required this.onRetry});
  final String? message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            message == null
                ? Icons.search_off_rounded
                : Icons.cloud_off_rounded,
            size: 58,
            color: AppColors.muted,
          ),
          const SizedBox(height: 12),
          Text(
            message ?? 'Không tìm thấy món phù hợp',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          TextButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('Thử lại'),
          ),
        ],
      ),
    ),
  );
}
