import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vi_viet/main.dart';
import 'package:vi_viet/services/api_client.dart';
import 'package:vi_viet/state/app_state.dart';

Widget _testApp() {
  final state = AppState(
    api: ApiClient(
      client: MockClient(
        (_) async =>
            http.Response('{"items":[],"page":1,"limit":100,"total":0}', 200),
      ),
    ),
  )..initialized = true;
  return ViVietApp(state: state);
}

Future<void> _pumpLogin(WidgetTester tester) async {
  await tester.binding.setSurfaceSize(const Size(430, 932));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(_testApp());
  await tester.pumpAndSettle();
}

Future<void> _openRegister(WidgetTester tester) async {
  final registerLink = find.text('Đăng ký ngay');
  await tester.scrollUntilVisible(
    registerLink,
    200,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.tap(registerLink);
  await tester.pumpAndSettle();
  expect(
    find.text('Tạo tài khoản để khám phá ẩm thực Việt Nam'),
    findsOneWidget,
  );
}

void _expectLoginScreen() {
  expect(find.text('Chào mừng bạn trở lại!'), findsOneWidget);
  expect(find.text('Đăng ký ngay'), findsOneWidget);
}

void main() {
  testWidgets('visible register back button returns to login', (tester) async {
    await _pumpLogin(tester);
    await _openRegister(tester);

    final backButton = find.byKey(const Key('register-back-button'));
    expect(backButton, findsOneWidget);
    await tester.tap(backButton);
    await tester.pumpAndSettle();

    _expectLoginScreen();
    expect(tester.takeException(), isNull);
  });

  testWidgets('login link at the bottom returns to login', (tester) async {
    await _pumpLogin(tester);
    await _openRegister(tester);

    final loginLink = find.text('Đã có tài khoản?  Đăng nhập');
    await tester.scrollUntilVisible(
      loginLink,
      300,
      scrollable: find.byType(Scrollable).last,
    );
    await tester.tap(loginLink);
    await tester.pumpAndSettle();

    _expectLoginScreen();
  });

  testWidgets('Android system back returns to login', (tester) async {
    await _pumpLogin(tester);
    await _openRegister(tester);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();

    _expectLoginScreen();
  });
}
