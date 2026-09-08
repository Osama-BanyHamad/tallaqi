// Platform-specific helpers for the recorder: where to write the file and how to read it back.
export 'recording_io.dart' if (dart.library.js_interop) 'recording_web.dart';
