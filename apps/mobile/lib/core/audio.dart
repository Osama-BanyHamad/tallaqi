import 'package:flutter/foundation.dart';
import 'package:just_audio/just_audio.dart';

import 'api.dart';
import 'prefs.dart';

/// Ayah audio: streamed per ayah from the reciter registry the server exposes (`/quran/reciters`).
/// Nothing is bundled; the app only plays URLs. One player for the whole app so a tap anywhere replaces what is playing.
class AyahAudio extends ChangeNotifier {
  AyahAudio._();
  static final AyahAudio I = AyahAudio._();

  final AudioPlayer _player = AudioPlayer();
  List<Map<String, dynamic>> reciters = const [];
  String pattern = '{surah:03d}{ayah:03d}.mp3';
  String reciterKey = 'husary';
  bool _loaded = false;

  /// Currently playing ayah (surah, ayah) or null.
  (int, int)? current;
  bool get playing => _player.playing;
  Stream<PlayerState> get state => _player.playerStateStream;

  Map<String, dynamic>? get reciter => reciters.cast<Map<String, dynamic>?>().firstWhere((r) => r?['key'] == reciterKey, orElse: () => reciters.isEmpty ? null : reciters.first);

  Future<void> load() async {
    if (_loaded) return;
    reciterKey = await Prefs.I.getString('audio.reciter') ?? reciterKey;
    try {
      final d = await Api.I.get('/quran/reciters') as Map<String, dynamic>;
      reciters = (d['reciters'] as List).cast<Map<String, dynamic>>();
      pattern = d['pattern'] ?? pattern;
      _loaded = true;
    } catch (_) {
      // keep defaults; the sheet will say audio is unavailable
    }
    _player.playerStateStream.listen((s) {
      if (s.processingState == ProcessingState.completed) {
        current = null;
      }
      notifyListeners();
    });
    notifyListeners();
  }

  bool get available => Api.I.can('quran.audio.use') && Api.I.moduleOn('quran.audio') && reciters.isNotEmpty;

  Future<void> setReciter(String key) async {
    reciterKey = key;
    await Prefs.I.setString('audio.reciter', key);
    notifyListeners();
  }

  String urlFor(int surah, int ayah) {
    final base = (reciter?['base'] ?? '') as String;
    final file = pattern.replaceAll('{surah:03d}', surah.toString().padLeft(3, '0')).replaceAll('{ayah:03d}', ayah.toString().padLeft(3, '0'));
    return '$base$file';
  }

  /// Play one ayah. Tapping the ayah that is playing stops it.
  Future<void> play(int surah, int ayah) async {
    if (current == (surah, ayah) && _player.playing) {
      await stop();
      return;
    }
    current = (surah, ayah);
    notifyListeners();
    try {
      await _player.setUrl(urlFor(surah, ayah));
      await _player.play();
    } catch (_) {
      current = null;
      notifyListeners();
      rethrow;
    }
  }

  /// Play a sequence of ayat in order (e.g. a plan segment or a page).
  Future<void> playAll(List<(int, int)> ayat) async {
    if (ayat.isEmpty) return;
    current = ayat.first;
    notifyListeners();
    try {
      await _player.setAudioSources([for (final a in ayat) AudioSource.uri(Uri.parse(urlFor(a.$1, a.$2)))]);
      _player.currentIndexStream.listen((i) {
        if (i != null && i < ayat.length) {
          current = ayat[i];
          notifyListeners();
        }
      });
      await _player.play();
    } catch (_) {
      current = null;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> stop() async {
    await _player.stop();
    current = null;
    notifyListeners();
  }

  Future<void> pause() => _player.pause();
  Future<void> resume() => _player.play();
}
