import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/dish.dart';
import '../models/history_entry.dart';
import '../models/user_profile.dart';
import '../services/api_client.dart';

class AppState extends ChangeNotifier {
  AppState({ApiClient? api}) : api = api ?? ApiClient();

  static const _dishCacheKey = 'dish_catalog_cache_v1';
  final ApiClient api;

  UserProfile? user;
  List<Dish> dishes = const [];
  List<Dish> favorites = const [];
  List<HistoryEntry> history = const [];
  bool initialized = false;
  bool dishesLoading = false;
  bool favoritesLoading = false;
  bool historyLoading = false;
  String? dishesError;

  bool get isAuthenticated => user != null;

  Future<void> initialize() async {
    await api.restoreSession();
    if (api.hasSession) {
      try {
        user = UserProfile.fromJson(await api.get('/users/me'));
      } catch (_) {
        await api.clearSession();
      }
    }
    initialized = true;
    notifyListeners();
  }

  Future<void> login(String email, String password) async {
    final payload = await api.post(
      '/auth/login',
      body: {'email': email.trim(), 'password': password},
    );
    await _acceptAuth(payload);
  }

  Future<void> register(String fullName, String email, String password) async {
    final payload = await api.post(
      '/auth/register',
      body: {
        'fullName': fullName.trim(),
        'email': email.trim(),
        'password': password,
      },
    );
    await _acceptAuth(payload);
  }

  Future<void> _acceptAuth(Map<String, dynamic> payload) async {
    await api.saveSession(
      payload['accessToken'] as String,
      payload['refreshToken'] as String,
    );
    user = UserProfile.fromJson(payload['user'] as Map<String, dynamic>);
    notifyListeners();
    try {
      await loadFavorites();
    } catch (_) {
      // Authentication succeeded even if optional account data is offline.
    }
    try {
      await loadHistory();
    } catch (_) {
      // Authentication succeeded even if optional account data is offline.
    }
  }

  Future<void> logout() async {
    final refresh = api.refreshToken;
    if (refresh != null) {
      try {
        await api.post('/auth/logout', body: {'refreshToken': refresh});
      } catch (_) {
        // Local logout must always succeed even when the server is offline.
      }
    }
    await api.clearSession();
    user = null;
    favorites = const [];
    history = const [];
    dishes = dishes.map((item) => item.copyWith(isFavorite: false)).toList();
    notifyListeners();
  }

  Future<void> updateProfile(String fullName) async {
    try {
      user = UserProfile.fromJson(
        await api.patch('/users/me', body: {'fullName': fullName.trim()}),
      );
      notifyListeners();
    } on ApiException catch (error) {
      await _expireIfUnauthorized(error);
      rethrow;
    }
  }

  Future<void> loadDishes({
    String query = '',
    String? region,
    String? category,
    String? difficulty,
    int? maxMinutes,
  }) async {
    dishesLoading = true;
    dishesError = null;
    notifyListeners();
    final params = <String, String>{'limit': '100'};
    if (query.trim().isNotEmpty) params['q'] = query.trim();
    if (region != null && region.isNotEmpty) params['region'] = region;
    if (category != null && category.isNotEmpty) params['category'] = category;
    if (difficulty != null && difficulty.isNotEmpty) {
      params['difficulty'] = difficulty;
    }
    if (maxMinutes != null) params['maxMinutes'] = '$maxMinutes';
    final cacheable =
        query.trim().isEmpty &&
        region == null &&
        category == null &&
        difficulty == null &&
        maxMinutes == null;
    final path = Uri(path: '/dishes', queryParameters: params).toString();
    try {
      final payload = await api.get(path);
      dishes = (payload['items'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(Dish.fromJson)
          .toList(growable: false);
      if (cacheable) {
        await _cacheDishes();
      }
    } on ApiException catch (error) {
      await _expireIfUnauthorized(error);
      dishesError = error.message;
      if (dishes.isEmpty &&
          query.isEmpty &&
          region == null &&
          category == null) {
        await _restoreDishCache();
      }
    } finally {
      dishesLoading = false;
      notifyListeners();
    }
  }

  Future<void> _cacheDishes() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(
        _dishCacheKey,
        jsonEncode(dishes.map((item) => item.toJson()).toList()),
      );
    } catch (_) {
      // Cache failure must not hide fresh server data.
    }
  }

  Future<void> _restoreDishCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_dishCacheKey);
      if (raw == null) return;
      dishes = (jsonDecode(raw) as List<dynamic>)
          .whereType<Map<String, dynamic>>()
          .map(Dish.fromJson)
          .toList(growable: false);
    } catch (_) {
      // Missing/corrupt cache is equivalent to no offline data.
    }
  }

  Future<Dish> loadDish(String slug) async {
    try {
      return Dish.fromJson(await api.get('/dishes/$slug'));
    } on ApiException catch (error) {
      await _expireIfUnauthorized(error);
      rethrow;
    }
  }

  Future<void> loadFavorites() async {
    if (!isAuthenticated) {
      favorites = const [];
      return;
    }
    favoritesLoading = true;
    notifyListeners();
    try {
      final payload = await api.get('/favorites');
      favorites = (payload['items'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(Dish.fromJson)
          .toList(growable: false);
      final slugs = favorites.map((item) => item.slug).toSet();
      dishes = dishes
          .map((item) => item.copyWith(isFavorite: slugs.contains(item.slug)))
          .toList(growable: false);
    } on ApiException catch (error) {
      await _expireIfUnauthorized(error);
      rethrow;
    } finally {
      favoritesLoading = false;
      notifyListeners();
    }
  }

  Future<void> toggleFavorite(Dish dish) async {
    if (!isAuthenticated) {
      throw const ApiException('Hãy đăng nhập để đồng bộ món yêu thích.');
    }
    final next = !dish.isFavorite;
    _setFavorite(dish, next);
    try {
      if (next) {
        await api.post('/favorites', body: {'dishSlug': dish.slug});
      } else {
        await api.delete('/favorites/${dish.slug}');
      }
    } on ApiException catch (error) {
      _setFavorite(dish, !next);
      await _expireIfUnauthorized(error);
      rethrow;
    }
  }

  void _setFavorite(Dish dish, bool value) {
    dishes = dishes
        .map(
          (item) =>
              item.slug == dish.slug ? item.copyWith(isFavorite: value) : item,
        )
        .toList(growable: false);
    if (value) {
      if (!favorites.any((item) => item.slug == dish.slug)) {
        favorites = [...favorites, dish.copyWith(isFavorite: true)];
      }
    } else {
      favorites = favorites
          .where((item) => item.slug != dish.slug)
          .toList(growable: false);
    }
    notifyListeners();
  }

  Future<void> loadHistory() async {
    if (!isAuthenticated) {
      history = const [];
      return;
    }
    historyLoading = true;
    notifyListeners();
    try {
      final payload = await api.get('/history');
      history = (payload['items'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(HistoryEntry.fromJson)
          .toList(growable: false);
    } on ApiException catch (error) {
      await _expireIfUnauthorized(error);
      rethrow;
    } finally {
      historyLoading = false;
      notifyListeners();
    }
  }

  Future<void> clearHistory() async {
    try {
      await api.delete('/history');
      history = const [];
      notifyListeners();
    } on ApiException catch (error) {
      await _expireIfUnauthorized(error);
      rethrow;
    }
  }

  Future<void> sendFeedback(String predictionId, String selectedDish) async {
    try {
      await api.post(
        '/predictions/$predictionId/feedback',
        body: {'selectedDish': selectedDish},
      );
      await loadHistory();
    } on ApiException catch (error) {
      await _expireIfUnauthorized(error);
      rethrow;
    }
  }

  Future<void> _expireIfUnauthorized(ApiException error) async {
    if (error.statusCode != 401) return;
    await api.clearSession();
    user = null;
    favorites = const [];
    history = const [];
    dishes = dishes.map((item) => item.copyWith(isFavorite: false)).toList();
    notifyListeners();
  }
}

class AppStateScope extends InheritedNotifier<AppState> {
  const AppStateScope({
    super.key,
    required AppState state,
    required super.child,
  }) : super(notifier: state);

  static AppState of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<AppStateScope>();
    assert(scope != null, 'AppStateScope is missing above this context');
    return scope!.notifier!;
  }
}
