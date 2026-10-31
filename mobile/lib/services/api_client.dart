import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

abstract final class ApiConfig {
  static const configuredBaseUrl = String.fromEnvironment('API_BASE_URL');

  static String get baseUrl {
    if (configuredBaseUrl.isNotEmpty) return configuredBaseUrl;
    if (kIsWeb) return 'http://127.0.0.1:8000';
    return defaultTargetPlatform == TargetPlatform.android
        ? 'http://10.0.2.2:8000'
        : 'http://127.0.0.1:8000';
  }

  static String resolveUrl(String value) {
    final uri = Uri.tryParse(value.trim());
    if (uri == null || value.trim().isEmpty) return value;
    if (uri.hasScheme) return uri.toString();
    return Uri.parse(baseUrl).resolveUri(uri).toString();
  }
}

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});
  final String message;
  final int? statusCode;
  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  static const _storage = FlutterSecureStorage();
  final http.Client _client;
  String? _accessToken;
  String? _refreshToken;

  bool get hasSession => _accessToken != null && _refreshToken != null;

  Future<void> restoreSession() async {
    try {
      _accessToken = await _storage.read(key: 'access_token');
      _refreshToken = await _storage.read(key: 'refresh_token');
    } catch (_) {
      _accessToken = null;
      _refreshToken = null;
    }
  }

  Future<void> saveSession(String access, String refresh) async {
    _accessToken = access;
    _refreshToken = refresh;
    try {
      await _storage.write(key: 'access_token', value: access);
      await _storage.write(key: 'refresh_token', value: refresh);
    } catch (_) {
      // The in-memory session remains usable if secure storage is unavailable.
    }
  }

  Future<void> clearSession() async {
    _accessToken = null;
    _refreshToken = null;
    try {
      await _storage.delete(key: 'access_token');
      await _storage.delete(key: 'refresh_token');
    } catch (_) {
      // Already cleared from memory.
    }
  }

  Future<Map<String, dynamic>> get(String path) => _request('GET', path);

  Future<Map<String, dynamic>> post(
    String path, {
    Map<String, dynamic>? body,
  }) => _request('POST', path, body: body);

  Future<Map<String, dynamic>> patch(
    String path, {
    required Map<String, dynamic> body,
  }) => _request('PATCH', path, body: body);

  Future<Map<String, dynamic>> delete(String path) => _request('DELETE', path);

  Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
    bool retry = true,
  }) async {
    try {
      final request = http.Request(
        method,
        Uri.parse('${ApiConfig.baseUrl}$path'),
      );
      request.headers['Accept'] = 'application/json';
      if (_accessToken != null) {
        request.headers['Authorization'] = 'Bearer $_accessToken';
      }
      if (body != null) {
        request.headers['Content-Type'] = 'application/json; charset=utf-8';
        request.body = jsonEncode(body);
      }
      final streamed = await _client
          .send(request)
          .timeout(const Duration(seconds: 20));
      final response = await http.Response.fromStream(streamed);
      if (response.statusCode == 401 && retry && await _refresh()) {
        return await _request(method, path, body: body, retry: false);
      }
      return _decode(response);
    } on TimeoutException {
      throw const ApiException('Kết nối quá thời gian. Vui lòng thử lại.');
    } on SocketException {
      throw const ApiException('Không thể kết nối máy chủ. Hãy kiểm tra mạng.');
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException('Không thể xử lý yêu cầu lúc này.');
    }
  }

  Future<Map<String, dynamic>> predict(XFile image, {bool retry = true}) async {
    try {
      final bytes = await image.readAsBytes();
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiConfig.baseUrl}/predict'),
      );
      if (_accessToken != null) {
        request.headers['Authorization'] = 'Bearer $_accessToken';
      }
      request.files.add(
        http.MultipartFile.fromBytes('image', bytes, filename: image.name),
      );
      final streamed = await _client
          .send(request)
          .timeout(const Duration(seconds: 90));
      final response = await http.Response.fromStream(streamed);
      if (response.statusCode == 401 && retry && await _refresh()) {
        return await predict(image, retry: false);
      }
      return _decode(response);
    } on TimeoutException {
      throw const ApiException('Nhận diện quá thời gian. Vui lòng thử lại.');
    } on SocketException {
      throw const ApiException(
        'Không thể kết nối backend. Hãy kiểm tra server và mạng.',
      );
    } on ApiException {
      rethrow;
    } catch (_) {
      throw const ApiException('Không thể nhận diện ảnh lúc này.');
    }
  }

  Map<String, dynamic> _decode(http.Response response) {
    final dynamic payload = response.bodyBytes.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = payload is Map<String, dynamic>
          ? payload['detail']?.toString()
          : null;
      throw ApiException(
        detail ?? 'Máy chủ trả về lỗi ${response.statusCode}.',
        statusCode: response.statusCode,
      );
    }
    return payload is Map<String, dynamic> ? payload : <String, dynamic>{};
  }

  Future<bool> _refresh() async {
    final refresh = _refreshToken;
    if (refresh == null) return false;
    try {
      final response = await _client
          .post(
            Uri.parse('${ApiConfig.baseUrl}/auth/refresh'),
            headers: {'Content-Type': 'application/json; charset=utf-8'},
            body: jsonEncode({'refreshToken': refresh}),
          )
          .timeout(const Duration(seconds: 15));
      if (response.statusCode != 200) {
        await clearSession();
        return false;
      }
      final payload =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      await saveSession(
        payload['accessToken'] as String,
        payload['refreshToken'] as String,
      );
      return true;
    } catch (_) {
      await clearSession();
      return false;
    }
  }

  String? get refreshToken => _refreshToken;
}
