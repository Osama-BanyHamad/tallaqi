/// Presentation helpers for Quran text. The text itself is never altered.
const basmalah = 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ';

({String? basmalah, String body}) splitBasmalah(String text, int surah, int ayah) {
  if (ayah == 1 && surah != 1 && surah != 9 && text.startsWith('$basmalah ')) {
    return (basmalah: basmalah, body: text.substring(basmalah.length + 1));
  }
  return (basmalah: null, body: text);
}

const stateAr = {
  'not_memorized': 'غير محفوظ', 'learning': 'قيد الحفظ', 'recent': 'حديث الحفظ', 'strong': 'متين', 'mastered': 'متقن',
  'needs_revision': 'يحتاج مراجعة', 'weak': 'ضعيف', 'critical': 'حرج',
};
const purposeAr = {'new': 'حفظ جديد', 'near': 'مراجعة قريبة', 'far': 'مراجعة بعيدة', 'assessment': 'اختبار'};
const outcomeAr = {'pass': 'اجتاز', 'repeat': 'يعيد', 'partial': 'جزئي'};
