import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vi_viet/models/dish.dart';
import 'package:vi_viet/screens/recipe_detail_screen.dart';
import 'package:vi_viet/services/api_client.dart';
import 'package:vi_viet/state/app_state.dart';

Map<String, dynamic> sourcedDishJson() => {
  'id': 25,
  'slug': 'pho',
  'name': 'Phở',
  'prepMinutes': 45,
  'cookMinutes': 210,
  'totalMinutes': 255,
  'servingsText': '6 phần',
  'hasRecipe': true,
  'isFavorite': false,
  'imageUrl': '/media/dishes/pho.webp',
  'imageAttribution': 'Tác giả ảnh · CC BY 4.0 · Wikimedia Commons',
  'imageAuthor': 'Tác giả ảnh',
  'imageSourceUrl': 'https://commons.wikimedia.org/wiki/File:Pho.jpg',
  'imageLicenseName': 'CC BY 4.0',
  'imageLicenseUrl': 'https://creativecommons.org/licenses/by/4.0/',
  'recipe': {
    'ingredients': [
      {'name': 'Bánh phở', 'quantity': '500', 'unit': 'g'},
    ],
    'steps': ['Nấu theo hướng dẫn từ nguồn.'],
    'sourceUrl': 'https://en.wikibooks.org/wiki/Cookbook:Phở_Bò',
    'sourceName': 'Wikibooks Cookbook – Phở Bò',
    'sourceRevisionUrl': 'https://en.wikibooks.org/w/index.php?title=Cookbook:Phở_Bò&oldid=4518483',
    'licenseName': 'CC BY-SA 4.0',
    'licenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0/',
    'attribution': 'Cộng đồng biên tập viên Wikibooks.',
    'modifiedFromSource': true,
    'contentOrigin': 'translated_open_source',
    'verificationStatus': 'source_verified',
    'verificationNote': 'Đã đối chiếu phiên bản cố định.',
    'references': [
      {
        'name': 'Cookbook:Phở Bò',
        'url': 'https://en.wikibooks.org/wiki/Cookbook:Phở_Bò',
        'publisher': 'Wikibooks',
        'accessedAt': '2026-10-10',
      },
    ],
  },
};

void main() {
  test(
    'parses recipe licensing, explicit time, servings, and image metadata',
    () {
      final dish = Dish.fromJson(sourcedDishJson());

      expect(dish.prepMinutes, 45);
      expect(dish.cookMinutes, 210);
      expect(dish.totalMinutes, 255);
      expect(dish.servingsText, '6 phần');
      expect(dish.recipe?.sourceRevisionUrl, contains('oldid=4518483'));
      expect(dish.recipe?.licenseName, 'CC BY-SA 4.0');
      expect(dish.recipe?.modifiedFromSource, isTrue);
      expect(dish.recipe?.contentOrigin, 'translated_open_source');
      expect(dish.recipe?.references.single.publisher, 'Wikibooks');
      expect(dish.imageLicenseName, 'CC BY 4.0');
    },
  );

  test('resolves relative media URLs and preserves absolute URLs', () {
    expect(
      ApiConfig.resolveUrl('/media/dishes/pho.webp'),
      '${ApiConfig.baseUrl}/media/dishes/pho.webp',
    );
    expect(
      ApiConfig.resolveUrl('https://example.com/pho.webp'),
      'https://example.com/pho.webp',
    );
  });

  test('formats minutes, hours, days, and no-cook recipes', () {
    expect(formatRecipeDuration(null), 'Chưa có');
    expect(formatRecipeDuration(35), '35 phút');
    expect(formatRecipeDuration(150), '2 giờ 30 phút');
    expect(formatRecipeDuration(4320), '3 ngày');
    expect(formatRecipeDuration(0, zeroMeansNoCook: true), 'Không cần nấu');
  });

  testWidgets('shows recipe and image source and license controls', (
    tester,
  ) async {
    final payload = sourcedDishJson()..['imageUrl'] = null;
    final state = AppState(
      api: ApiClient(
        client: MockClient(
          (_) async => http.Response(
            jsonEncode(payload),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          ),
        ),
      ),
    );
    const summary = Dish(
      id: 25,
      slug: 'pho',
      name: 'Phở',
      hasRecipe: true,
      isFavorite: false,
    );

    await tester.pumpWidget(
      MaterialApp(
        home: AppStateScope(
          state: state,
          child: const RecipeDetailScreen(dish: summary),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('recipe-time-summary')), findsOneWidget);
    expect(find.text('Sơ chế'), findsOneWidget);
    expect(find.text('Nấu'), findsOneWidget);
    expect(find.text('Tổng'), findsOneWidget);
    expect(find.text('45 phút'), findsOneWidget);
    expect(find.text('3 giờ 30 phút'), findsOneWidget);
    expect(find.text('4 giờ 15 phút'), findsOneWidget);
    expect(find.byKey(const Key('source-license-section')), findsOneWidget);
    expect(find.text('Nguồn & bản quyền'), findsOneWidget);
    expect(find.text('Công thức gốc'), findsOneWidget);
    expect(find.text('Phiên bản đã dùng'), findsOneWidget);
    expect(find.text('Nguồn ảnh'), findsOneWidget);
    expect(find.text('Dịch và chuẩn hóa từ nguồn mở.'), findsOneWidget);
    expect(find.text('Nguồn tham khảo'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('time summary does not overflow on a narrow phone', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(320, 640));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final payload = sourcedDishJson()..['imageUrl'] = null;
    final state = AppState(
      api: ApiClient(
        client: MockClient(
          (_) async => http.Response(
            jsonEncode(payload),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          ),
        ),
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: AppStateScope(
          state: state,
          child: const RecipeDetailScreen(
            dish: Dish(
              id: 25,
              slug: 'pho',
              name: 'Phở',
              hasRecipe: true,
              isFavorite: false,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('recipe-time-summary')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
