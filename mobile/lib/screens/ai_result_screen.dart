import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../models/prediction.dart';
import '../services/api_client.dart';
import '../state/app_state.dart';
import '../theme/app_theme.dart';
import 'recipe_detail_screen.dart';

class AiResultScreen extends StatefulWidget {
  const AiResultScreen({
    super.key,
    required this.imageBytes,
    required this.result,
  });

  final Uint8List imageBytes;
  final PredictionResponse result;

  @override
  State<AiResultScreen> createState() => _AiResultScreenState();
}

class _AiResultScreenState extends State<AiResultScreen> {
  bool _sending = false;
  bool _feedbackSent = false;

  Future<void> _openRecipe() async {
    final dish = widget.result.recognizedDish;
    if (dish == null) return;
    await Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => RecipeDetailScreen(dish: dish)));
  }

  Future<void> _sendFeedback(String selectedDish) async {
    final id = widget.result.predictionId;
    if (id == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Hãy đăng nhập để gửi phản hồi.')),
        );
      }
      return;
    }
    setState(() => _sending = true);
    try {
      await AppStateScope.of(context).sendFeedback(id, selectedDish);
      if (mounted) {
        setState(() => _feedbackSent = true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã ghi nhận món đúng. Cảm ơn bạn!')),
        );
      }
    } on ApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.message)));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _showCorrectionSheet() async {
    final state = AppStateScope.of(context);
    if (state.dishes.isEmpty) await state.loadDishes();
    if (!mounted) return;
    var query = '';
    final selected = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.cream,
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setSheetState) {
          final normalized = query.trim().toLowerCase();
          final items = state.dishes
              .where(
                (dish) =>
                    normalized.isEmpty ||
                    dish.name.toLowerCase().contains(normalized) ||
                    dish.aliases.any(
                      (alias) => alias.toLowerCase().contains(normalized),
                    ),
              )
              .toList(growable: false);
          return DraggableScrollableSheet(
            expand: false,
            initialChildSize: .7,
            minChildSize: .45,
            maxChildSize: .92,
            builder: (context, controller) => Padding(
              padding: EdgeInsets.fromLTRB(
                20,
                14,
                20,
                MediaQuery.viewInsetsOf(context).bottom + 16,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 42,
                      height: 4,
                      decoration: BoxDecoration(
                        color: AppColors.line,
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  Text(
                    'Chọn món đúng',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    autofocus: true,
                    decoration: const InputDecoration(
                      hintText: 'Tìm trong 38 món...',
                      prefixIcon: Icon(Icons.search_rounded),
                    ),
                    onChanged: (value) => setSheetState(() => query = value),
                  ),
                  const SizedBox(height: 10),
                  Expanded(
                    child: ListView.builder(
                      controller: controller,
                      itemCount: items.length,
                      itemBuilder: (context, index) => ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text(items[index].name),
                        trailing: const Icon(Icons.chevron_right_rounded),
                        onTap: () =>
                            Navigator.pop(sheetContext, items[index].name),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
    if (selected != null && mounted) await _sendFeedback(selected);
  }

  @override
  Widget build(BuildContext context) {
    final recognizedDish = widget.result.recognizedDish;
    final displayName = recognizedDish?.name ?? widget.result.prediction.dish;
    final confidence = widget.result.prediction.confidence;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kết quả AI'),
        centerTitle: true,
        backgroundColor: AppColors.cream,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 6, 20, 32),
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(24),
            child: Image.memory(
              widget.imageBytes,
              height: 250,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: Text(
                  displayName,
                  key: const Key('recognized-dish-name'),
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: AppColors.forest.withValues(alpha: .1),
                  borderRadius: BorderRadius.circular(30),
                ),
                child: Text(
                  '${(confidence * 100).toStringAsFixed(1)}%',
                  style: const TextStyle(
                    color: AppColors.forest,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Kết quả có xác suất cao nhất từ ảnh bạn đã chọn.',
            style: Theme.of(context).textTheme.bodyLarge
                ?.copyWith(color: AppColors.muted, height: 1.45),
          ),
          const SizedBox(height: 24),
          Material(
            key: const Key('open-recipe-card'),
            color: recognizedDish == null
                ? AppColors.line.withValues(alpha: .35)
                : AppColors.creamStrong,
            borderRadius: BorderRadius.circular(20),
            child: InkWell(
              onTap: recognizedDish == null ? null : _openRecipe,
              borderRadius: BorderRadius.circular(20),
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Row(
                  children: [
                    const Icon(
                      Icons.menu_book_rounded,
                      color: AppColors.forest,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            recognizedDish == null
                                ? 'Không tìm thấy công thức'
                                : 'Xem công thức $displayName',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            recognizedDish == null
                                ? 'Nhãn AI chưa ánh xạ được với danh mục món.'
                                : 'Mở nguyên liệu, cách làm và nguồn tham khảo.',
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ],
                      ),
                    ),
                    if (recognizedDish != null)
                      const Icon(Icons.arrow_forward_rounded),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),
          Center(
            child: TextButton(
              key: const Key('wrong-result-link'),
              onPressed: _sending || _feedbackSent
                  ? null
                  : _showCorrectionSheet,
              child: Text(
                _feedbackSent ? 'Đã gửi phản hồi' : 'Kết quả chưa đúng?',
              ),
            ),
          ),
          const SizedBox(height: 18),
          ElevatedButton.icon(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.camera_alt_outlined),
            label: const Text('Chụp ảnh khác'),
          ),
        ],
      ),
    );
  }
}
