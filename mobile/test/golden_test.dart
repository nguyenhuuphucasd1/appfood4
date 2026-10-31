import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:vi_viet/main.dart';
import 'package:vi_viet/services/api_client.dart';
import 'package:vi_viet/screens/main_shell.dart';
import 'package:vi_viet/state/app_state.dart';
import 'package:vi_viet/theme/app_theme.dart';

void main() {
  testWidgets('renders the primary mobile screens', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final fontLoader = FontLoader('RobotoApp')
      ..addFont(rootBundle.load('assets/fonts/Roboto-Regular.ttf'))
      ..addFont(rootBundle.load('assets/fonts/Roboto-Medium.ttf'))
      ..addFont(rootBundle.load('assets/fonts/Roboto-Bold.ttf'));
    await fontLoader.load();
    final iconLoader = FontLoader('MaterialIcons')
      ..addFont(rootBundle.load('assets/fonts/MaterialIcons.otf'));
    await iconLoader.load();
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    final state = AppState(
      api: ApiClient(
        client: MockClient(
          (_) async => http.Response(
            '{"items":[],"page":1,"limit":100,"total":0}',
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          ),
        ),
      ),
    )..initialized = true;
    await tester.pumpWidget(ViVietApp(state: state));
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('goldens/login_screen.png'),
    );

    await tester.tap(find.text('Tiếp tục với tư cách khách'));
    await tester.pumpAndSettle();
    await expectLater(
      find.byType(Scaffold),
      matchesGoldenFile('goldens/home_screen.png'),
    );
  });

  testWidgets('renders responsive desktop navigation', (tester) async {
    SharedPreferences.setMockInitialValues({});
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(1200, 800);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.view.resetPhysicalSize);
    final state = AppState(
      api: ApiClient(
        client: MockClient(
          (_) async => http.Response(
            '{"items":[{"id":1,"slug":"pho","name":"Phở","hasRecipe":false,"isFavorite":false},{"id":2,"slug":"bun-bo-hue","name":"Bún bò Huế","hasRecipe":false,"isFavorite":false}],"page":1,"limit":100,"total":2}',
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          ),
        ),
      ),
    )..initialized = true;

    await tester.pumpWidget(
      AppStateScope(
        state: state,
        child: MaterialApp(theme: AppTheme.light, home: const MainShell()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(NavigationRail), findsOneWidget);
    await expectLater(
      find.byType(Scaffold).last,
      matchesGoldenFile('goldens/home_desktop.png'),
    );
  });
}
