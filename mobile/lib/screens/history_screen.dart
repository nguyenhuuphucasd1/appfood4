import 'package:flutter/material.dart';

import '../models/history_entry.dart';
import '../services/api_client.dart';
import '../state/app_state.dart';
import '../theme/app_theme.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) AppStateScope.of(context).loadHistory();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = AppStateScope.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Lịch sử nhận diện'),
        actions: [
          if (state.history.isNotEmpty)
            IconButton(
              onPressed: _clear,
              tooltip: 'Xóa lịch sử',
              icon: const Icon(Icons.delete_outline_rounded),
            ),
        ],
      ),
      body: state.historyLoading && state.history.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : state.history.isEmpty
          ? const Center(child: Text('Chưa có lần nhận diện nào được lưu.'))
          : RefreshIndicator(
              onRefresh: state.loadHistory,
              child: ListView.separated(
                padding: const EdgeInsets.all(20),
                itemCount: state.history.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (context, index) =>
                    _HistoryCard(item: state.history[index]),
              ),
            ),
    );
  }

  Future<void> _clear() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Xóa toàn bộ lịch sử?'),
        content: const Text('Thao tác này không thể hoàn tác.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Xóa'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await AppStateScope.of(context).clearHistory();
    } on ApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.message)));
      }
    }
  }
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard({required this.item});
  final HistoryEntry item;

  @override
  Widget build(BuildContext context) {
    final corrected =
        item.selectedDish != null && item.selectedDish != item.predictedDish;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              radius: 26,
              backgroundColor: AppColors.forest.withValues(alpha: .1),
              child: const Icon(
                Icons.auto_awesome_rounded,
                color: AppColors.forest,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.selectedDish ?? item.predictedDish,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Độ tin cậy ${(item.confidence * 100).toStringAsFixed(1)}%',
                  ),
                  if (corrected)
                    Text(
                      'AI dự đoán: ${item.predictedDish}',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  Text(
                    _formatDate(item.createdAt),
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const Text(
                    'Ảnh gốc không được lưu',
                    style: TextStyle(fontSize: 11, color: AppColors.muted),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  static String _formatDate(DateTime value) {
    final local = value.toLocal();
    String two(int number) => number.toString().padLeft(2, '0');
    return '${two(local.hour)}:${two(local.minute)} · ${two(local.day)}/${two(local.month)}/${local.year}';
  }
}
