import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vi_viet/models/prediction.dart';
import 'package:vi_viet/screens/ai_result_screen.dart';
import 'package:vi_viet/screens/recipe_detail_screen.dart';
import 'package:vi_viet/services/api_client.dart';
import 'package:vi_viet/state/app_state.dart';

final _image = base64Decode(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
);

Map<String, dynamic> _dish({bool detail = false}) => {
  'id': 25,
  'slug': 'pho',
  'name': 'Phở',
  'hasRecipe': true,
  'isFavorite': false,
  if (detail) 'recipe': null,
  if (detail) 'recipeMessage': 'Đang cập nhật.',
};

void main() {
  testWidgets('shows only top one and opens its exact recipe', (tester) async {
    final api = ApiClient(
      client: MockClient(
        (_) async => http.Response(
          jsonEncode(_dish(detail: true)),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        ),
      ),
    );
    final state = AppState(api: api);
    final result = PredictionResponse.fromJson({
      'prediction': {'dish': 'Pho', 'confidence': .997, 'accepted': true},
      'top3': [
        {'dish': 'Pho', 'confidence': .997},
        {'dish': 'Banh mi', 'confidence': .002},
        {'dish': 'Bun bo Hue', 'confidence': .001},
      ],
      'canonicalDish': 'pho',
      'recognizedDish': _dish(),
    });

    await tester.pumpWidget(
      AppStateScope(
        state: state,
        child: MaterialApp(
          home: AiResultScreen(
            imageBytes: Uint8List.fromList(_image),
            result: result,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Phở'), findsOneWidget);
    expect(find.text('99.7%'), findsOneWidget);
    expect(find.text('Các kết quả khác'), findsNothing);
    expect(find.text('Banh mi'), findsNothing);
    expect(find.text('Xem công thức Phở'), findsOneWidget);

    await tester.tap(find.byKey(const Key('open-recipe-card')));
    await tester.pumpAndSettle();
    expect(find.byType(RecipeDetailScreen), findsOneWidget);
  });

  testWidgets('disables recipe card when model label cannot be mapped', (
    tester,
  ) async {
    final result = PredictionResponse.fromJson({
      'prediction': {'dish': 'Unknown food', 'confidence': .42},
      'top3': const [],
      'canonicalDish': '',
      'recognizedDish': null,
    });
    await tester.pumpWidget(
      AppStateScope(
        state: AppState(),
        child: MaterialApp(
          home: AiResultScreen(
            imageBytes: Uint8List.fromList(_image),
            result: result,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Không tìm thấy công thức'), findsOneWidget);
    expect(find.textContaining('chưa ánh xạ'), findsOneWidget);
  });
}
