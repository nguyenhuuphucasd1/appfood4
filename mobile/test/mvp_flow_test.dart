import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:image_picker/image_picker.dart';
import 'package:vi_viet/models/dish.dart';
import 'package:vi_viet/services/ai_service.dart';
import 'package:vi_viet/services/api_client.dart';
import 'package:vi_viet/state/app_state.dart';

http.Response response(Object body, [int status = 200]) => http.Response(
  jsonEncode(body),
  status,
  headers: {'content-type': 'application/json; charset=utf-8'},
);

void main() {
  test('register → predict → feedback → favorite → history → logout', () async {
    var feedbackSaved = false;
    var favoriteSaved = false;
    final api = ApiClient(
      client: MockClient((request) async {
        final path = request.url.path;
        if (path == '/auth/register') {
          return response({
            'accessToken': 'access',
            'refreshToken': 'refresh',
            'user': {
              'id': 1,
              'email': 'an@example.com',
              'fullName': 'Nguyễn An',
            },
          }, 201);
        }
        if (path == '/predict') {
          return response({
            'prediction': {'dish': 'Phở', 'confidence': .91, 'accepted': true},
            'top3': [
              {'dish': 'Phở', 'confidence': .91},
              {'dish': 'Bún bò Huế', 'confidence': .06},
            ],
            'canonicalDish': 'pho',
            'recognizedDish': {
              'id': 25,
              'slug': 'pho',
              'name': 'Phở',
              'hasRecipe': true,
              'isFavorite': false,
            },
            'predictionId': 'prediction-1',
            'recipe': null,
            'recipeMessage': 'Chưa có công thức đã kiểm chứng cho món này.',
          });
        }
        if (path == '/predictions/prediction-1/feedback') {
          feedbackSaved = true;
          return response({
            'id': 'prediction-1',
            'predictedDish': 'Phở',
            'confidence': .91,
            'top3': [],
            'selectedDish': 'Phở',
            'imageStored': false,
            'createdAt': '2026-10-05T12:00:00Z',
          });
        }
        if (path == '/favorites' && request.method == 'POST') {
          favoriteSaved = true;
          return response({
            'id': 1,
            'slug': 'pho',
            'name': 'Phở',
            'hasRecipe': false,
            'isFavorite': true,
          }, 201);
        }
        if (path == '/favorites') {
          return response({
            'items': favoriteSaved
                ? [
                    {
                      'id': 1,
                      'slug': 'pho',
                      'name': 'Phở',
                      'hasRecipe': false,
                      'isFavorite': true,
                    },
                  ]
                : [],
          });
        }
        if (path == '/history') {
          return response({
            'items': feedbackSaved
                ? [
                    {
                      'id': 'prediction-1',
                      'predictedDish': 'Phở',
                      'confidence': .91,
                      'top3': [],
                      'selectedDish': 'Phở',
                      'imageStored': false,
                      'createdAt': '2026-10-05T12:00:00Z',
                    },
                  ]
                : [],
          });
        }
        if (path == '/auth/logout') return response({}, 204);
        return response({'detail': 'not found'}, 404);
      }),
    );
    final state = AppState(api: api);

    await state.register('Nguyễn An', 'an@example.com', 'password123');
    expect(state.isAuthenticated, isTrue);

    final prediction = await AiService(api).predict(
      XFile.fromData(
        Uint8List.fromList([1, 2, 3]),
        name: 'food.png',
        mimeType: 'image/png',
      ),
    );
    expect(prediction.predictionId, 'prediction-1');
    expect(prediction.recognizedDish?.name, 'Phở');
    expect(prediction.recipe, isNull);

    await state.sendFeedback(prediction.predictionId!, 'Phở');
    const dish = Dish(
      id: 1,
      slug: 'pho',
      name: 'Phở',
      hasRecipe: false,
      isFavorite: false,
    );
    state.dishes = const [dish];
    await state.toggleFavorite(dish);
    await state.loadHistory();

    expect(feedbackSaved, isTrue);
    expect(state.favorites.single.slug, 'pho');
    expect(state.history.single.imageStored, isFalse);

    await state.logout();
    expect(state.isAuthenticated, isFalse);
    expect(state.history, isEmpty);
  });
}
