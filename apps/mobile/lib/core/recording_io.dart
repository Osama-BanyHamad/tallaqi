import 'dart:io';

import 'package:path_provider/path_provider.dart';

Future<String> recordingPath() async => '${(await getTemporaryDirectory()).path}/talaqqi_recitation_${DateTime.now().millisecondsSinceEpoch}.m4a';

Future<List<int>> readRecording(String path) => File(path).readAsBytes();

Future<void> discardRecording(String path) async {
  try {
    await File(path).delete();
  } catch (_) {}
}
