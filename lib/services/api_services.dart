import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiServices {
  ApiServices({http.Client? client})
    : _client = client ?? http.Client(),
      baseUrl = const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://localhost:5000',
      );

  final http.Client _client;
  final String baseUrl;
  static const _timeout = Duration(seconds: 10);

  Future<Map<String, dynamic>?> getLatestReading() async {
    final response = await _client
        .get(Uri.parse('$baseUrl/api/sensor-readings/latest'))
        .timeout(_timeout);
    final body = _decodeResponse(response);
    return body['reading'] as Map<String, dynamic>?;
  }

  Future<List<Map<String, dynamic>>> getRecentReadings({int limit = 24}) async {
    final response = await _client
        .get(Uri.parse('$baseUrl/api/sensor-readings?limit=$limit'))
        .timeout(_timeout);
    final body = _decodeResponse(response);
    return (body['readings'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> getPrediction(
    String crop,
    Map<String, dynamic> sensorData,
  ) async {
    final url = Uri.parse("$baseUrl/predict");
    final response = await _client
        .post(
          url,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'crop': crop, 'features': sensorData}),
        )
        .timeout(_timeout);
    return _decodeResponse(response);
  }

  Map<String, dynamic> _decodeResponse(http.Response response) {
    final decoded = jsonDecode(response.body);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('The server returned an invalid response.');
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        decoded['error']?.toString() ??
            'The server request failed (${response.statusCode}).',
      );
    }
    return decoded;
  }
}

class ApiException implements Exception {
  const ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}
