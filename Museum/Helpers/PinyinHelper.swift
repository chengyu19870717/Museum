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
        let pinyin = toPinyin(text)
        // Split by non-letter characters, take first letter of each word
        let components = pinyin.components(separatedBy: CharacterSet.letters.inverted)
        return components
            .filter { !$0.isEmpty }
            .compactMap { $0.first }
            .map { String($0) }
            .joined()
    }

    /// Check if query matches text via Chinese, full pinyin, or pinyin initials
    static func matches(_ text: String, query: String) -> Bool {
        guard !query.isEmpty else { return true }
        let lowerQuery = query.lowercased()

        // 1. Direct Chinese text match (e.g., searching "故宫" matches "故宫博物院")
        if text.lowercased().contains(lowerQuery) {
            return true
        }

        // 2. Full pinyin match (e.g., "gugong" matches "故宫博物院")
        let fullPinyin = toPinyin(text)
        if fullPinyin.contains(lowerQuery) {
            return true
        }

        // 3. Pinyin initials match (e.g., "ggbwy" matches "故宫博物院")
        let initials = toPinyinInitials(text)
        if initials.contains(lowerQuery) {
            return true
        }

        return false
    }

    /// Check if query fuzzy-matches any of the given texts
    static func matchesAny(_ texts: [String], query: String) -> Bool {
        guard !query.isEmpty else { return true }
        return texts.contains { matches($0, query: query) }
    }
}