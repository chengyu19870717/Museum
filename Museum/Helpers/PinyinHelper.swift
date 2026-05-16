import Foundation

struct PinyinHelper {
    /// Convert Chinese text to full pinyin (e.g., "故宫" -> "gugong")
    static func toPinyin(_ text: String) -> String {
        let mutableString = NSMutableString(string: text)
        // Transform Chinese characters to Latin alphabet with tone marks
        CFStringTransform(mutableString, nil, kCFStringTransformToLatin, false)
        // Strip tone marks/diacritics
        CFStringTransform(mutableString, nil, kCFStringTransformStripDiacritics, false)
        return (mutableString as String).lowercased()
    }

    /// Get pinyin first letters (e.g., "故宫博物院" -> "ggbwy")
    static func toPinyinInitials(_ text: String) -> String {
        toPinyinInitials(fromPinyin: toPinyin(text))
    }

    /// Same as above but accepts a pre-computed pinyin string to avoid a redundant CFStringTransform.
    static func toPinyinInitials(fromPinyin pinyin: String) -> String {
        pinyin.components(separatedBy: CharacterSet.letters.inverted)
            .filter { !$0.isEmpty }
            .compactMap { $0.first }
            .map { String($0) }
            .joined()
    }

    static func compactLetters(_ text: String) -> String {
        text.lowercased()
            .unicodeScalars
            .filter { CharacterSet.letters.union(.decimalDigits).contains($0) }
            .map(String.init)
            .joined()
    }

    /// Build a reusable search blob so large lists do not re-run pinyin conversion on every keystroke.
    static func searchBlob(for text: String) -> String {
        let lowercased = text.lowercased()
        let pinyin = toPinyin(text)                          // single CFStringTransform
        let compactPinyin = compactLetters(pinyin)
        let initials = toPinyinInitials(fromPinyin: pinyin)  // reuse — no second transform
        return [lowercased, pinyin, compactPinyin, initials]
            .filter { !$0.isEmpty }
            .joined(separator: " ")
    }

    static func normalizedQuery(_ query: String) -> String {
        query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    }

}
