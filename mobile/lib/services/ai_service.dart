import 'package:image_picker/image_picker.dart';

import '../models/prediction.dart';
import 'api_client.dart';

export 'api_client.dart' show ApiConfig;

class AiServiceException implements Exception {
  const AiServiceException(this.message);
  final String message;
  @override
  String toString() => message;
}

class AiService {
  const AiService(this.client);
  final ApiClient client;

  Future<PredictionResponse> predict(XFile image) async {
    try {
      return PredictionResponse.fromJson(await client.predict(image));
    } on ApiException catch (error) {
      throw AiServiceException(error.message);
    }
  }
}
