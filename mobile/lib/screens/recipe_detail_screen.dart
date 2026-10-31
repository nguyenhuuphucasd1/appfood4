import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/dish.dart';
import '../services/api_client.dart';
import '../state/app_state.dart';
import '../theme/app_theme.dart';
import '../widgets/dish_image.dart';

String formatRecipeDuration(int? minutes, {bool zeroMeansNoCook = false}) {
  if (minutes == null) return 'Chưa có';
  if (minutes == 0) return zeroMeansNoCook ? 'Không cần nấu' : '0 phút';
  if (minutes < 60) return '$minutes phút';

  final days = minutes ~/ (24 * 60);
  final remainingAfterDays = minutes % (24 * 60);
  final hours = remainingAfterDays ~/ 60;
  final remainingMinutes = remainingAfterDays % 60;
  final parts = <String>[];
  if (days > 0) parts.add('$days ngày');
  if (hours > 0) parts.add('$hours giờ');
  if (remainingMinutes > 0) parts.add('$remainingMinutes phút');
  return parts.join(' ');
}

class RecipeDetailScreen extends StatefulWidget {
  const RecipeDetailScreen({super.key, required this.dish});
  final Dish dish;

  @override
  State<RecipeDetailScreen> createState() => _RecipeDetailScreenState();
}

class _RecipeDetailScreenState extends State<RecipeDetailScreen> {
  Dish? _detail;
  String? _error;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_detail == null && _error == null) _load();
  }

  Future<void> _load() async {
    try {
      final detail = await AppStateScope.of(context).loadDish(widget.dish.slug);
      if (mounted) setState(() => _detail = detail);
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    }
  }

  Future<void> _favorite() async {
    final dish = _detail ?? widget.dish;
    try {
      await AppStateScope.of(context).toggleFavorite(dish);
      if (mounted) {
        setState(() => _detail = dish.copyWith(isFavorite: !dish.isFavorite));
      }
    } on ApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.message)));
      }
    }
  }

  Future<void> _openUrl(String value) async {
    var opened = false;
    try {
      final uri = Uri.tryParse(value);
      opened =
          uri != null &&
          (uri.scheme == 'http' || uri.scheme == 'https') &&
          await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      opened = false;
    }
    if (!opened && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Không thể mở liên kết này.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final dish = _detail ?? widget.dish;
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar.large(
            expandedHeight: 320,
            pinned: true,
            backgroundColor: AppColors.cream,
            leading: Padding(
              padding: const EdgeInsets.all(8),
              child: CircleAvatar(
                backgroundColor: Colors.white,
                child: BackButton(onPressed: () => Navigator.pop(context)),
              ),
            ),
            actions: [
              Padding(
                padding: const EdgeInsets.all(8),
                child: IconButton.filled(
                  onPressed: _favorite,
                  tooltip: dish.isFavorite
                      ? 'Bỏ yêu thích'
                      : 'Thêm vào yêu thích',
                  style: IconButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: AppColors.orange,
                  ),
                  icon: Icon(
                    dish.isFavorite
                        ? Icons.favorite_rounded
                        : Icons.favorite_border_rounded,
                  ),
                ),
              ),
            ],
            flexibleSpace: FlexibleSpaceBar(
              background: DishImage(name: dish.name, imageUrl: dish.imageUrl),
            ),
          ),
          SliverToBoxAdapter(
            child: Transform.translate(
              offset: const Offset(0, -22),
              child: Container(
                padding: const EdgeInsets.fromLTRB(22, 28, 22, 36),
                decoration: const BoxDecoration(
                  color: AppColors.cream,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
                ),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 900),
                    child: _content(dish),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _content(Dish dish) {
    if (_error != null) {
      return Column(
        children: [
          const Icon(Icons.cloud_off_rounded, size: 48, color: AppColors.muted),
          const SizedBox(height: 12),
          Text(_error!, textAlign: TextAlign.center),
          TextButton.icon(
            onPressed: () {
              setState(() => _error = null);
              _load();
            },
            icon: const Icon(Icons.refresh),
            label: const Text('Thử lại'),
          ),
        ],
      );
    }
    if (_detail == null) {
      return const Center(child: CircularProgressIndicator());
    }
    final recipe = dish.recipe;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(dish.name, style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 10),
        if (dish.description != null)
          Text(
            dish.description!,
            style: Theme.of(context).textTheme.bodyLarge
                ?.copyWith(color: AppColors.muted, height: 1.5),
          ),
        const SizedBox(height: 22),
        _TimeSummary(dish: dish),
        const SizedBox(height: 18),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: _Info(
                icon: Icons.signal_cellular_alt_rounded,
                label: 'Độ khó',
                value: dish.difficulty ?? 'Chưa có',
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _Info(
                icon: Icons.people_outline_rounded,
                label: 'Khẩu phần',
                value:
                    dish.servingsText ??
                    (dish.servings == null
                        ? 'Chưa có'
                        : '${dish.servings} người'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        if (recipe == null)
          _MissingRecipe(message: dish.recipeMessage)
        else ...[
          Text('Nguyên liệu', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 10),
          ...recipe.ingredients.map(
            (item) => ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(
                Icons.check_circle_outline,
                color: AppColors.forest,
              ),
              title: Text(item.name),
              trailing: Text(
                [item.quantity, item.unit]
                    .whereType<String>()
                    .where((value) => value.isNotEmpty)
                    .join(' '),
              ),
            ),
          ),
          const SizedBox(height: 18),
          Text('Cách làm', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 10),
          ...recipe.steps.indexed.map(
            (entry) => Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  CircleAvatar(
                    radius: 16,
                    backgroundColor: AppColors.forest,
                    foregroundColor: Colors.white,
                    child: Text('${entry.$1 + 1}'),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(entry.$2, style: const TextStyle(height: 1.5)),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          _SourceAndLicense(dish: dish, recipe: recipe, onOpen: _openUrl),
        ],
      ],
    );
  }
}

class _TimeSummary extends StatelessWidget {
  const _TimeSummary({required this.dish});

  final Dish dish;

  @override
  Widget build(BuildContext context) => Container(
    key: const Key('recipe-time-summary'),
    width: double.infinity,
    padding: const EdgeInsets.fromLTRB(10, 16, 10, 14),
    decoration: BoxDecoration(
      color: AppColors.creamStrong,
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: AppColors.line),
    ),
    child: Column(
      children: [
        const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.schedule_rounded, color: AppColors.forest, size: 20),
            SizedBox(width: 7),
            Text('Thời gian', style: TextStyle(fontWeight: FontWeight.w700)),
          ],
        ),
        const SizedBox(height: 13),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: _TimeMetric(
                label: 'Sơ chế',
                value: formatRecipeDuration(dish.prepMinutes),
              ),
            ),
            const _TimeDivider(),
            Expanded(
              child: _TimeMetric(
                label: 'Nấu',
                value: formatRecipeDuration(
                  dish.cookMinutes,
                  zeroMeansNoCook: true,
                ),
              ),
            ),
            const _TimeDivider(),
            Expanded(
              child: _TimeMetric(
                label: 'Tổng',
                value: formatRecipeDuration(dish.totalMinutes),
              ),
            ),
          ],
        ),
      ],
    ),
  );
}

class _TimeMetric extends StatelessWidget {
  const _TimeMetric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 3),
    child: Column(
      children: [
        Text(
          label,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 5),
        Text(
          value,
          maxLines: 2,
          textAlign: TextAlign.center,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontWeight: FontWeight.w700, height: 1.15),
        ),
      ],
    ),
  );
}

class _TimeDivider extends StatelessWidget {
  const _TimeDivider();

  @override
  Widget build(BuildContext context) =>
      Container(width: 1, height: 45, color: AppColors.line);
}

class _SourceAndLicense extends StatelessWidget {
  const _SourceAndLicense({
    required this.dish,
    required this.recipe,
    required this.onOpen,
  });

  final Dish dish;
  final RecipeData recipe;
  final Future<void> Function(String url) onOpen;

  @override
  Widget build(BuildContext context) => Container(
    key: const Key('source-license-section'),
    width: double.infinity,
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: AppColors.creamStrong,
      borderRadius: BorderRadius.circular(22),
      border: Border.all(color: AppColors.line),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.verified_outlined, color: AppColors.forest),
            const SizedBox(width: 9),
            Expanded(
              child: Text(
                'Nguồn & bản quyền',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        Text(
          'Công thức: ${recipe.sourceName}',
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 5),
        Text(
          recipe.contentOrigin == 'original_synthesis'
              ? 'Vị Việt biên soạn và đối chiếu nguồn.'
              : 'Dịch và chuẩn hóa từ nguồn mở.',
          style: const TextStyle(color: AppColors.forest),
        ),
        if (recipe.verificationNote.isNotEmpty) ...[
          const SizedBox(height: 5),
          Text(recipe.verificationNote),
        ],
        if (recipe.attribution.isNotEmpty) ...[
          const SizedBox(height: 5),
          Text(recipe.attribution),
        ],
        const SizedBox(height: 8),
        Wrap(
          spacing: 6,
          runSpacing: 4,
          children: [
            if (recipe.contentOrigin != 'original_synthesis') ...[
              _SourceLink(
                label: 'Công thức gốc',
                url: recipe.sourceUrl,
                onOpen: onOpen,
              ),
              _SourceLink(
                label: 'Phiên bản đã dùng',
                url: recipe.sourceRevisionUrl,
                onOpen: onOpen,
              ),
            ],
            _SourceLink(
              label: recipe.licenseName,
              url: recipe.licenseUrl,
              onOpen: onOpen,
            ),
          ],
        ),
        if (recipe.references.isNotEmpty) ...[
          const Divider(height: 28),
          const Text(
            'Nguồn tham khảo',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          ...recipe.references.map(
            (reference) => Material(
              type: MaterialType.transparency,
              child: ListTile(
                contentPadding: EdgeInsets.zero,
                dense: true,
                title: Text(reference.name),
                subtitle: Text(
                  '${reference.publisher} · Truy cập ${reference.accessedAt}',
                ),
                trailing: const Icon(Icons.open_in_new_rounded, size: 18),
                onTap: () => onOpen(reference.url),
              ),
            ),
          ),
        ],
        if (dish.imageAuthor != null || dish.imageAttribution != null) ...[
          const Divider(height: 28),
          Text(
            'Ảnh: ${dish.imageAuthor ?? dish.imageAttribution}',
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          if (dish.imageAttribution != null &&
              dish.imageAttribution != dish.imageAuthor) ...[
            const SizedBox(height: 5),
            Text(dish.imageAttribution!),
          ],
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: [
              if (dish.imageSourceUrl != null)
                _SourceLink(
                  label: 'Nguồn ảnh',
                  url: dish.imageSourceUrl!,
                  onOpen: onOpen,
                ),
              if (dish.imageLicenseUrl != null)
                _SourceLink(
                  label: dish.imageLicenseName ?? 'Giấy phép ảnh',
                  url: dish.imageLicenseUrl!,
                  onOpen: onOpen,
                ),
            ],
          ),
        ],
      ],
    ),
  );
}

class _SourceLink extends StatelessWidget {
  const _SourceLink({
    required this.label,
    required this.url,
    required this.onOpen,
  });

  final String label;
  final String url;
  final Future<void> Function(String url) onOpen;

  @override
  Widget build(BuildContext context) => TextButton.icon(
    onPressed: url.isEmpty ? null : () => onOpen(url),
    icon: const Icon(Icons.open_in_new_rounded, size: 17),
    label: Text(label.isEmpty ? 'Xem giấy phép' : label),
  );
}

class _MissingRecipe extends StatelessWidget {
  const _MissingRecipe({this.message});
  final String? message;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: AppColors.creamStrong,
      borderRadius: BorderRadius.circular(22),
      border: Border.all(color: AppColors.line),
    ),
    child: Row(
      children: [
        const CircleAvatar(
          backgroundColor: Colors.white,
          child: Icon(Icons.menu_book_outlined, color: AppColors.forest),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Text(
            message ?? 'Chưa có công thức đã kiểm chứng cho món này.',
          ),
        ),
      ],
    ),
  );
}

class _Info extends StatelessWidget {
  const _Info({required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Icon(icon, color: AppColors.forest),
      const SizedBox(height: 6),
      Text(label, style: Theme.of(context).textTheme.bodyMedium),
      const SizedBox(height: 3),
      Text(
        value,
        textAlign: TextAlign.center,
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
    ],
  );
}
