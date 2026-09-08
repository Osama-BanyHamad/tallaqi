import 'package:http/http.dart' as http;

/// On the web the recorder returns a blob URL; the file lives in the browser.
Future<String> recordingPath() async => '';

Future<List<int>> readRecording(String path) => http.readBytes(Uri.parse(path));

Future<void> discardRecording(String path) async {}
