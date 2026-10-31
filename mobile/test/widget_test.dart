import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vi_viet/main.dart';
import 'package:vi_viet/services/api_client.dart';
import 'package:vi_viet/state/app_state.dart';

void main() {
  testWidgets('opens the Vị Việt login screen', (tester) async {
    final state = AppState(
      api: ApiClient(
        client: MockClient(
          (_) async =>
              http.Response('{"items":[],"page":1,"limit":100,"total":0}', 200),
        ),
      ),
    )..initialized = true;
    await tester.pumpWidget(ViVietApp(state: state));
    await tester.pumpAndSettle();

    expect(find.bySemanticsLabel('Logo Vị Việt'), findsOneWidget);
    expect(find.text('Đăng nhập'), findsNWidgets(2));
    expect(find.text('Đăng ký ngay'), findsOneWidget);
    expect(find.text('Tiếp tục với tư cách khách'), findsOneWidget);
  });
}
