import Foundation
import SwiftUI

enum AppLanguage: String, CaseIterable, Codable {
    case zhHans = "zh-Hans"      // 简体中文
    case en = "en"                // English
    case fr = "fr"                // Français
    case ja = "ja"                // 日本語
    case ko = "ko"                // 한국어
    case la = "la"                // Latina
    case zhHant = "zh-Hant"      // 繁體中文

    var displayName: String {
        switch self {
        case .zhHans: return "简体中文"
        case .en:     return "English"
        case .fr:     return "Français"
        case .ja:     return "日本語"
        case .ko:     return "한국어"
        case .la:     return "Latina"
        case .zhHant: return "繁體中文"
        }
    }

    var nativeDisplayName: String {
        switch self {
        case .zhHans: return "简体中文"
        case .en:     return "English"
        case .fr:     return "Français"
        case .ja:     return "日本語"
        case .ko:     return "한국어"
        case .la:     return "Latina"
        case .zhHant: return "繁體中文"
        }
    }

    var flag: String {
        switch self {
        case .zhHans: return "🇨🇳"
        case .en:     return "🇬🇧"
        case .fr:     return "🇫🇷"
        case .ja:     return "🇯🇵"
        case .ko:     return "🇰🇷"
        case .la:     return "🏛️"
        case .zhHant: return "🇹🇼"
        }
    }
}

@MainActor
class LanguageManager: ObservableObject {
    static let shared = LanguageManager()

    private let languageKey = "appLanguage"

    @Published var currentLanguage: AppLanguage {
        didSet {
            UserDefaults.standard.set(currentLanguage.rawValue, forKey: languageKey)
        }
    }

    private init() {
        let saved = UserDefaults.standard.string(forKey: languageKey) ?? "zh-Hans"
        currentLanguage = AppLanguage(rawValue: saved) ?? .zhHans
    }

    func setLanguage(_ language: AppLanguage) {
        currentLanguage = language
    }
}