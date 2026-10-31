import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vi_viet/models/dish.dart';
import 'package:vi_viet/services/api_client.dart';
import 'package:vi_viet/state/app_state.dart';

http.Response jsonResponse(Object body, [int status = 200]) => http.Response(
  jsonEncode(body),
  status,
  headers: {'content-type': 'application/json; charset=utf-8'},
);

void main() {
  test(
    'loads dishes with search and filters encoded in the API request',
    () async {
      Uri? captured;
      final state = AppState(
        api: ApiClient(
          client: MockClient((request) async {
            captured = request.url;
            return jsonResponse({
              'items': [],
              'page': 1,
              'limit': 100,
              'total': 0,
            });
          }),
        ),
      );

      await state.loadDishes(
        query: 'bun bo hue',
        region: 'Miền Trung',
        category: 'Món chính',
        difficulty: 'Dễ',
        maxMinutes: 60,
      );

      expect(captured?.path, '/dishes');
      expect(captured?.queryParameters['q'], 'bun bo hue');
      expect(captured?.queryParameters['region'], 'Miền Trung');
      expect(captured?.queryParameters['category'], 'Món chính');
      expect(captured?.queryParameters['difficulty'], 'Dễ');
      expect(captured?.queryParameters['maxMinutes'], '60');
      expect(state.dishesLoading, isFalse);
    },
  );

  test('refreshes an expired access token and retries once', () async {
    var profileCalls = 0;
    var refreshCalls = 0;
    final api = ApiClient(
      client: MockClient((request) async {
        if (request.url.path == '/auth/refresh') {
          refreshCalls++;
          return jsonResponse({
            'accessToken': 'fresh-access',
            'refreshToken': 'fresh-refresh',
          });
        }
        if (request.url.path == '/users/me') {
          profileCalls++;
          if (profileCalls == 1) {
            return jsonResponse({'detail': 'expired'}, 401);
          }
          expect(request.headers['Authorization'], 'Bearer fresh-access');
          return jsonResponse({
            'id': 1,
            'email': 'an@example.com',
            'fullName': 'An',
          });
        }
        return jsonResponse({'detail': 'not found'}, 404);
      }),
    );
    await api.saveSession('expired-access', 'valid-refresh');

    final profile = await api.get('/users/me');

    expect(profile['fullName'], 'An');
    expect(profileCalls, 2);
    expect(refreshCalls, 1);
  });

  test('favorite update rolls back when the server rejects it', () async {
    final state = AppState(
      api: ApiClient(
        client: MockClient((request) async {
          if (request.url.path == '/auth/login') {
            return jsonResponse({
              'accessToken': 'access',
              'refreshToken': 'refresh',
              'user': {'id': 1, 'email': 'an@example.com', 'fullName': 'An'},
            });
          }
          if (request.url.path == '/favorites' && request.method == 'GET') {
            return jsonResponse({'items': []});
          }
          if (request.url.path == '/history') {
            return jsonResponse({'items': []});
          }
          if (request.url.path == '/favorites') {
            return jsonResponse({'detail': 'failed'}, 500);
          }
          return jsonResponse({});
        }),
      ),
    );
    await state.login('an@example.com', 'password123');
    const dish = Dish(
      id: 1,
      slug: 'pho',
      name: 'Phở',
      hasRecipe: false,
      isFavorite: false,
    );
    state.dishes = const [dish];

    await expectLater(state.toggleFavorite(dish), throwsA(isA<ApiException>()));

    expect(state.dishes.single.isFavorite, isFalse);
    expect(state.favorites, isEmpty);
  });
}
