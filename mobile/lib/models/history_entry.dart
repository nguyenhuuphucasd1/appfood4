import 'prediction.dart';

class HistoryEntry {
  const HistoryEntry({
    required this.id,
    required this.predictedDish,
    required this.confidence,
    required this.top3,
    required this.createdAt,
    required this.imageStored,
    this.selectedDish,
  });

  final String id;
  final String predictedDish;
  final double confidence;
  final List<FoodPrediction> top3;
  final String? selectedDish;
  final DateTime createdAt;
  final bool imageStored;

  factory HistoryEntry.fromJson(Map<String, dynamic> json) => HistoryEntry(
    id: json['id'] as String? ?? '',
    predictedDish: json['predictedDish'] as String? ?? '',
    confidence: (json['confidence'] as num? ?? 0).toDouble(),
    top3: (json['top3'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(FoodPrediction.fromJson)
        .toList(growable: false),
    selectedDish: json['selectedDish'] as String?,
    createdAt:
        DateTime.tryParse(json['createdAt'] as String? ?? '') ??
        DateTime.fromMillisecondsSinceEpoch(0),
    imageStored: json['imageStored'] as bool? ?? false,
  );
}
