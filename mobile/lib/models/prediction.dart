import 'dish.dart';

class FoodPrediction {
  const FoodPrediction({
    required this.dish,
    required this.confidence,
    this.accepted,
  });

  final String dish;
  final double confidence;
  final bool? accepted;

  factory FoodPrediction.fromJson(Map<String, dynamic> json) => FoodPrediction(
    dish: json['dish'] as String? ?? 'Không xác định',
    confidence: (json['confidence'] as num? ?? 0).toDouble(),
    accepted: json['accepted'] as bool?,
  );
}

class PredictionResponse {
  const PredictionResponse({
    required this.prediction,
    required this.top3,
    required this.canonicalDish,
    this.recognizedDish,
    this.recipe,
    this.recipeMessage,
    this.predictionId,
  });

  final FoodPrediction prediction;
  final List<FoodPrediction> top3;
  final String canonicalDish;
  final Dish? recognizedDish;
  final Object? recipe;
  final String? recipeMessage;
  final String? predictionId;

  factory PredictionResponse.fromJson(Map<String, dynamic> json) {
    final rawTop = json['top3'] as List<dynamic>? ?? const [];
    return PredictionResponse(
      prediction: FoodPrediction.fromJson(
        json['prediction'] as Map<String, dynamic>? ?? const {},
      ),
      top3: rawTop
          .whereType<Map<String, dynamic>>()
          .map(FoodPrediction.fromJson)
          .toList(growable: false),
      canonicalDish: json['canonicalDish'] as String? ?? '',
      recognizedDish: json['recognizedDish'] is Map<String, dynamic>
          ? Dish.fromJson(json['recognizedDish'] as Map<String, dynamic>)
          : null,
      recipe: json['recipe'],
      recipeMessage: json['recipeMessage'] as String?,
      predictionId: json['predictionId'] as String?,
    );
  }
}
